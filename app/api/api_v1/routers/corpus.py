import logging

from fastapi import APIRouter, HTTPException, Request, status

from app.api.api_v1.query_params import (
    get_query_params_as_dict,
    set_default_query_params,
    validate_query_params,
)
from app.errors import (
    AuthorisationError,
    ConflictError,
    RepositoryError,
    ValidationError,
)
from app.model.corpus import (
    CorpusCreateDTO,
    CorpusLogoUploadDTO,
    CorpusReadDTO,
    CorpusWriteDTO,
)
from app.service import corpus as corpus_service

corpora_router = r = APIRouter()

_LOGGER = logging.getLogger(__file__)


@r.get(
    "/corpora/{import_id}",
    response_model=CorpusReadDTO,
)
async def get_corpus(import_id: str) -> CorpusReadDTO:
    """
    Returns a specific corpus given the import id.

    :param str import_id: Specified corpus import_id.
    :raises HTTPException: If the corpus is not found a 404 is returned.
    :return CorpusReadDTO: returns a CorpusReadDTO of the corpus found.
    """
    try:
        corpus = corpus_service.get(import_id)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if corpus is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Corpus not found: {import_id}",
        )

    return corpus


@r.get("/corpora", response_model=list[CorpusReadDTO])
async def get_all_corpora(request: Request) -> list[CorpusReadDTO]:
    """
    Returns all corpora

    :param Request request: Request object.
    :return CorpusReadDTO: returns a CorpusReadDTO of the corpora found.
    """
    try:
        return corpus_service.all(request.state.user)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@r.get("/corpora/", response_model=list[CorpusReadDTO])
async def search_corpora(request: Request) -> list[CorpusReadDTO]:
    """
    Searches for corpora matching URL parameters ("q" by default).

    :param Request request: The fields to match against and the values
        to search for. Defaults to searching for "" in corpus titles and
        descriptions.
    :raises HTTPException: If invalid fields passed a 400 is returned.
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[CorpusReadDTO]: A list of matching corpora (which
        can be empty).
    """
    query_params = get_query_params_as_dict(request.query_params)

    query_params = set_default_query_params(query_params)

    VALID_PARAMS = ["q", "max_results"]
    validate_query_params(query_params, VALID_PARAMS)

    try:
        corpora = corpus_service.search(query_params, request.state.user)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except TimeoutError:
        msg = "Request timed out fetching matching corpora. Try adjusting your query."
        _LOGGER.error(msg)
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=msg,
        )

    if len(corpora) == 0:
        _LOGGER.info(f"Corpora not found for terms: {query_params}")

    return corpora


@r.put(
    "/corpora/{import_id}",
    response_model=CorpusReadDTO,
)
async def update_corpus(
    request: Request, import_id: str, new_corpus: CorpusWriteDTO
) -> CorpusReadDTO:
    """
    Updates a specific corpus given the import id.

    :param Request request: Request object.
    :param str import_id: Specified corpus import_id.
    :raises HTTPException: If the corpus is not found a 404 is returned.
    :return CorpusReadDTO: returns a CorpusReadDTO of the corpus updated.
    """
    try:
        corpus = corpus_service.update(import_id, new_corpus, request.state.user)
    except AuthorisationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if corpus is None:
        detail = f"Corpus not updated: {import_id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return corpus


@r.post("/corpora", response_model=str, status_code=status.HTTP_201_CREATED)
async def create_corpus(request: Request, new_corpus: CorpusCreateDTO) -> str:
    """Create a specific corpus given the import id.

    :param Request request: Request object.
    :param CorpusCreateDTO new_corpus: New corpus data object.
    :raises HTTPException: If there is an error raised during validation
        or during adding the corpus to the db.
    :return str: returns the import id of the newly created corpus.
    """
    try:
        corpus_id = corpus_service.create(new_corpus, request.state.user)
    except AuthorisationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)

    return corpus_id


@r.post("/corpora/{corpus_id}/upload-url", response_model=CorpusLogoUploadDTO)
async def get_upload_url(corpus_id: str) -> CorpusLogoUploadDTO:
    """Get a presigned URL for uploading a corpus logo.

    :param corpus_id: The ID of the corpus to upload a logo for
    :param user_context: The user context from the request
    :return: Upload URLs for the logo
    """
    _LOGGER.info(f"Getting upload URL for corpus {corpus_id}")
    try:
        return corpus_service.get_upload_url(corpus_id)
    except AuthorisationError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except Exception as e:
        _LOGGER.error(f"Error getting upload URL for corpus {corpus_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
