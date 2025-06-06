from fastapi import APIRouter, HTTPException, Request, status

from app.errors import AuthorisationError, RepositoryError, ValidationError
from app.model.corpus_type import CorpusTypeCreateDTO, CorpusTypeReadDTO
from app.service import corpus_type as corpus_type_service

corpus_types_router = APIRouter()


@corpus_types_router.get(
    "/corpus-types",
    response_model=list[CorpusTypeReadDTO],
)
async def get_all_corpus_types(request: Request) -> list[CorpusTypeReadDTO]:
    """Retrieve all corpus types.

    :param Request request: Request object.
    :raises HTTPException: If the corpus type is not found.
    :return CorpusTypeReadDTO: The requested corpus type.
    """
    try:
        return corpus_type_service.all(request.state.user)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@corpus_types_router.get(
    "/corpus-types/{corpus_type_name}",
    response_model=CorpusTypeReadDTO,
)
async def get_corpus_type(corpus_type_name: str) -> CorpusTypeReadDTO:
    """Retrieve a specific corpus type by its name.

    :param str corpus_type_name: The ID of the corpus type to retrieve.
    :raises HTTPException: If the corpus type is not found.
    :return CorpusTypeReadDTO: The requested corpus type.
    """
    try:
        corpus_type = corpus_type_service.get(corpus_type_name)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if corpus_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Corpus type not found: {corpus_type_name}",
        )
    return corpus_type


@corpus_types_router.post(
    "/corpus-types",
    response_model=str,
    status_code=status.HTTP_201_CREATED,
)
async def create_corpus_type(
    request: Request, new_corpus_type: CorpusTypeCreateDTO
) -> str:
    """Create a new corpus type.

    :param Request request: Request object.
    :param CorpusTypeCreateDTO new_corpus_type: New corpus type data.
    :raises HTTPException: If there is an error during creation.
    :return str: The created corpus type.
    """

    try:
        return corpus_type_service.create(new_corpus_type)
    except AuthorisationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
