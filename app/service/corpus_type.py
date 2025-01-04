import logging
from typing import Optional

from pydantic import ConfigDict, validate_call
from sqlalchemy.orm import Session

import app.clients.db.session as db_session
from app.model.corpus_type import CorpusTypeReadDTO
from app.model.user import UserContext
from app.repository import corpus_type as corpus_type_repo
from app.service import app_user

_LOGGER = logging.getLogger(__name__)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def all(user: UserContext) -> list[CorpusTypeReadDTO]:
    """
    Gets the entire list of corpora from the repository.

    :param UserContext user: The current user context.
    :return list[CorpusReadDTO]: The list of corpora.
    """
    with db_session.get_db() as db:
        org_id = app_user.restrict_entities_to_user_org(user)
        return corpus_type_repo.all(db, org_id)


@validate_call(config=ConfigDict(arbitrary_types_allowed=True))
def get(
    corpus_type_name: str, db: Optional[Session] = None
) -> Optional[CorpusTypeReadDTO]:
    """Retrieve a corpus type by ID.

    :param str corpus_type_name: The name of the corpus type to retrieve.
    :return CorpusTypeReadDTO: The requested corpus type.
    :raises RepositoryError: If there is an error during retrieval.
    """
    if db is None:
        db = db_session.get_db()

    return corpus_type_repo.get(db, corpus_type_name)
