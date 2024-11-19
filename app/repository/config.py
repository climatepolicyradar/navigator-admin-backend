import logging
from typing import Any, Sequence

from db_client.models.base import AnyModel
from db_client.models.dfce.family import Variant
from db_client.models.dfce.geography import Geography
from db_client.models.document.physical_document import Language
from db_client.models.organisation import Corpus, CorpusType, Organisation
from sqlalchemy.orm import Session

from app.model.config import ConfigReadDTO, CorpusData, DocumentConfig
from app.model.user import UserContext

_LOGGER = logging.getLogger(__name__)


def _tree_table_to_json(
    table: AnyModel,
    db: Session,
) -> list[dict]:
    json_out = []
    child_list_map: dict[int, Any] = {}

    for row in db.query(table).order_by(table.id).all():
        row_object = {col.name: getattr(row, col.name) for col in row.__table__.columns}
        row_children: list[dict[str, Any]] = []
        child_list_map[row_object["id"]] = row_children

        # No parent indicates a top level element
        node_row_object = {"node": row_object, "children": row_children}
        node_id = row_object["parent_id"]
        if node_id is None:
            json_out.append(node_row_object)
        else:
            append_list = child_list_map.get(node_id)
            if append_list is None:
                raise RuntimeError(f"Could not locate parent node with id {node_id}")
            append_list.append(node_row_object)

    return json_out


def _to_corpus_data(row) -> CorpusData:
    return CorpusData(
        corpus_import_id=row.corpus_import_id,
        title=row.title,
        description=row.description,
        corpus_type=row.corpus_type,
        corpus_type_description=row.corpus_type_description,
        organisation={"name": row.org_name, "id": row.org_id},
        taxonomy={**row.taxonomy},
    )


def get_corpora(db: Session, user: UserContext) -> Sequence[CorpusData]:
    corpora = (
        db.query(
            Corpus.import_id.label("corpus_import_id"),
            Corpus.title.label("title"),
            Corpus.description.label("description"),
            Corpus.corpus_type_name.label("corpus_type"),
            CorpusType.description.label("corpus_type_description"),
            Organisation.name.label("org_name"),
            Organisation.id.label("org_id"),
            CorpusType.valid_metadata.label("taxonomy"),
        )
        .join(
            Corpus,
            Corpus.corpus_type_name == CorpusType.name,
        )
        .join(Organisation, Organisation.id == Corpus.organisation_id)
    )
    if user.is_superuser:
        corpora = corpora.all()
    else:
        corpora = corpora.filter(Organisation.id == user.org_id).all()

    return [_to_corpus_data(row) for row in corpora]


def get(db: Session, user: UserContext) -> ConfigReadDTO:
    """
    Returns the configuration for the admin service.

    :param Session db: connection to the database
    :return ConfigReadDTO: The config data
    """

    geographies = _tree_table_to_json(table=Geography, db=db)
    corpora = get_corpora(db, user)
    languages = {lang.language_code: lang.name for lang in db.query(Language).all()}

    corpus_types = get_unique_corpus_types(corpora)

    # Now Document config
    doc_config = DocumentConfig(
        variants=[
            variant.variant_name
            for variant in db.query(Variant).order_by(Variant.variant_name).all()
        ],
    )

    return ConfigReadDTO(
        geographies=geographies,
        corpora=corpora,
        corpus_types=corpus_types,
        languages=languages,
        document=doc_config,
    )


def get_unique_corpus_types(corpora):
    """Generate a list of unique corpus type dictionaries.

    :param List[Corpus] corpora: List of corpus items.
    :return List[Dict[str, Any]]: List of unique corpus type
        dictionaries.
    """
    corpus_types = [
        {
            "name": c.corpus_type,
            "description": c.corpus_type_description,
        }
        for c in corpora
    ]
    # Use frozenset to create a unique set of dictionaries
    unique_corpus_types = {frozenset(ct.items()) for ct in corpus_types}
    corpus_types = [dict(t) for t in unique_corpus_types]
    return corpus_types
