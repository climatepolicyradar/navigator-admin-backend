import logging
from typing import Optional, cast

from db_client.models.organisation import CorpusType, Organisation
from sqlalchemy import asc
from sqlalchemy.exc import MultipleResultsFound
from sqlalchemy.orm import Session

from app.errors import RepositoryError
from app.model.corpus_type import CorpusTypeCreateDTO, CorpusTypeReadDTO

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


def get(db: Session, corpus_type_name: str) -> Optional[CorpusTypeReadDTO]:
    """Get a corpus type from the database given a name.

    :param db Session: The database connection.
    :param str corpus_type_name: The ID of the corpus type to retrieve.
    :return CorpusTypeReadDTO: The requested corpus type.
    :raises RepositoryError: If the corpus type is not found.
    """
    try:
        corpus_type = (
            db.query(CorpusType)
            .filter(CorpusType.name == corpus_type_name)
            .one_or_none()
        )
        return _corpus_type_to_dto(corpus_type) if corpus_type is not None else None

    except MultipleResultsFound as e:
        _LOGGER.error(e)
        raise RepositoryError(e)


def create(db: Session, corpus_type: CorpusTypeCreateDTO) -> str:
    """Create a new corpus type.

    :param db Session: The database connection.
    :param CorpusTypeCreateDTO corpus_type: The values for the new
        corpus type.
    :return str: The name of the newly created corpus type.
    """
    new_corpus_type = CorpusType(
        name=corpus_type.name,
        description=corpus_type.description,
        valid_metadata=corpus_type.metadata,
    )

    try:
        db.add(new_corpus_type)
        db.commit()
    except Exception as e:
        _LOGGER.exception("Error trying to create Corpus Type")
        raise RepositoryError(e)

    return cast(str, new_corpus_type.name)
