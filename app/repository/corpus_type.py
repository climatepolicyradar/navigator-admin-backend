import logging
from typing import Optional, cast

from db_client.models.organisation import CorpusType, Organisation
from sqlalchemy import Session, asc
from sqlalchemy.exc import MultipleResultsFound, NoResultFound

from app.errors import RepositoryError
from app.model.corpus_type import CorpusTypeReadDTO

_LOGGER = logging.getLogger(__name__)


def _corpus_type_to_dto(corpus_type: CorpusType) -> CorpusTypeReadDTO:
    """Convert a CorpusType model to a CorpusTypeReadDTO.

    :param CorpusType corpus_type: The corpus type model.
    :return CorpusTypeReadDTO: The corresponding DTO.
    """
    return CorpusTypeReadDTO(
        name=str(corpus_type.name),
        description=str(corpus_type.description),
        metadata=cast(dict, corpus_type.valid_metadata),
    )


def all(db: Session, org_id: Optional[int]) -> list[CorpusTypeReadDTO]:
    """Get a list of all corpus types in the database.

    :param db Session: The database connection.
    :param org_id int: the ID of the organisation the user belongs to
    :return CorpusTypeReadDTO: The requested corpus type.
    :raises RepositoryError: If the corpus type is not found.
    """
    query = db.query(CorpusType)
    if org_id is not None:
        query = query.filter(Organisation.id == org_id)

    result = query.order_by(asc(CorpusType.name)).all()

    if not result:
        return []

    return [_corpus_type_to_dto(corpus_type) for corpus_type in result]


def get(db: Session, corpus_type_name: str) -> CorpusTypeReadDTO:
    """Get a corpus type from the database given a name.

    :param db Session: The database connection.
    :param str corpus_type_name: The ID of the corpus type to retrieve.
    :return CorpusTypeReadDTO: The requested corpus type.
    :raises RepositoryError: If the corpus type is not found.
    """
    try:
        corpus_type = (
            db.query(CorpusType).filter(CorpusType.name == corpus_type_name).one()
        )
        return _corpus_type_to_dto(corpus_type)

    except (MultipleResultsFound, NoResultFound) as e:
        _LOGGER.error(e)
        raise RepositoryError(e)
