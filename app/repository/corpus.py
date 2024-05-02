import logging
from typing import Optional

from db_client.models.organisation.corpus import Corpus
from sqlalchemy.orm import Session

_LOGGER = logging.getLogger(__name__)


def get_corpus_org_id(db: Session, corpus_id: str) -> Optional[int]:
    """Get the organisation ID a corpus belongs to.

    TODO: Will need to review as part of PDCT-1011.

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
