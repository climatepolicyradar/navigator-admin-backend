import logging
from typing import Any, Optional

from db_client.models.base import AnyModel
from db_client.models.dfce.family import (
    FamilyDocumentRole,
    FamilyDocumentType,
    FamilyEventType,
    Variant,
)
from db_client.models.dfce.geography import Geography
from db_client.models.dfce.metadata import MetadataOrganisation, MetadataTaxonomy
from db_client.models.document.physical_document import Language
from db_client.models.organisation.users import Organisation
from sqlalchemy.orm import Session

from app.model.config import ConfigReadDTO, DocumentConfig, EventConfig, TaxonomyData

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


def _get_organisation_taxonomy_by_name(
    db: Session, org_name: str
) -> Optional[TaxonomyData]:
    """
    Returns the TaxonomyConfig for the named organisation

    :param Session db: connection to the database
    :return TaxonomyConfig: the TaxonomyConfig from the db
    """
    metadata = (
        db.query(MetadataTaxonomy.valid_metadata)
        .join(
            MetadataOrganisation,
            MetadataOrganisation.taxonomy_id == MetadataTaxonomy.id,
        )
        .join(Organisation, Organisation.id == MetadataOrganisation.organisation_id)
        .filter_by(name=org_name)
        .one_or_none()
    )
    if metadata is not None:
        return metadata[0]


def get(db: Session) -> ConfigReadDTO:
    """
    Returns the configuration for the admin service.

    :param Session db: connection to the database
    :return ConfigReadDTO: The config data
    """

    geographies = _tree_table_to_json(table=Geography, db=db)
    taxonomies = {}

    # Be resilient to an organisation not having a taxonomy
    for org in db.query(Organisation).all():
        tax = _get_organisation_taxonomy_by_name(db=db, org_name=org.name)
        if tax is not None:
            taxonomies[org.name] = tax

    languages = {lang.language_code: lang.name for lang in db.query(Language).all()}

    # Now Document config
    doc_config = DocumentConfig(
        roles=[
            doc_role.name
            for doc_role in db.query(FamilyDocumentRole)
            .order_by(FamilyDocumentRole.name)
            .all()
        ],
        types=[
            doc_type.name
            for doc_type in db.query(FamilyDocumentType)
            .order_by(FamilyDocumentType.name)
            .all()
        ],
        variants=[
            variant.variant_name
            for variant in db.query(Variant).order_by(Variant.variant_name).all()
        ],
    )

    # Now Event config
    event_config = EventConfig(
        types=[
            event_type.name
            for event_type in db.query(FamilyEventType)
            .order_by(FamilyEventType.name)
            .all()
        ]
    )
    return ConfigReadDTO(
        geographies=geographies,
        taxonomies=taxonomies,
        languages=languages,
        document=doc_config,
        event=event_config,
    )
