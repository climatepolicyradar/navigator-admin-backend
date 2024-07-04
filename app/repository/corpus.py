import logging
from typing import Optional

from db_client.models.organisation import Corpus, CorpusType
from sqlalchemy.orm import Session

from app.errors import ValidationError
from app.model.config import TaxonomyData

_LOGGER = logging.getLogger(__name__)


def get_corpus_org_id(db: Session, corpus_id: str) -> Optional[int]:
    """Get the organisation ID a corpus belongs to.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to get the org
        for.
    :return Optional[int]: Return the organisation ID the given corpus
        belongs to or None.
    """
    return db.query(Corpus.organisation_id).filter_by(import_id=corpus_id).scalar()


def validate(db: Session, corpus_id: str) -> bool:
    """Validate whether a corpus with the given ID exists in the DB.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to validate.
    :return bool: Return whether or not the corpus exists in the DB.
    """
    corpora = [corpus[0] for corpus in db.query(Corpus.import_id).distinct().all()]
    return bool(corpus_id in corpora)


def get_taxonomy_from_corpus(
    db: Session, corpus_id: str, _entity_key: Optional[str] = None
) -> Optional[TaxonomyData]:
    """Get the taxonomy of a corpus.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to get the taxonomy
        for.
    :return Optional[str]: Return the taxonomy of the given corpus or None.
    """
    tax = (
        db.query(CorpusType.valid_metadata)
        .join(Corpus, Corpus.corpus_type_name == CorpusType.name)
        .filter(Corpus.import_id == corpus_id)
        .scalar()
    )
    if tax is not None and _entity_key is not None:
        if _entity_key not in tax.keys():
            raise ValidationError(
                f"Cannot find {_entity_key} taxonomy data in database"
            )
        tax = tax[_entity_key]
    return tax
