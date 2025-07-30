import logging

from fastapi import APIRouter, HTTPException, status

from app.errors import RepositoryError, ValidationError
from app.model.organisation import (
    OrganisationCreateDTO,
    OrganisationReadDTO,
    OrganisationWriteDTO,
)
from app.service import organisation as organisation_service

organisations_router = APIRouter()

_LOGGER = logging.getLogger(__name__)


@organisations_router.get(
    "/organisations",
    response_model=list[OrganisationReadDTO],
)
async def get_all_organisations() -> list[OrganisationReadDTO]:
    """Retrieve all organisations.

    :raises HTTPException: If the corpus type is not found.
    :return CorpusTypeReadDTO: The requested corpus type.
    """
    try:
        return organisation_service.all()
    except RepositoryError as e:
        _LOGGER.error(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@organisations_router.get(
    "/organisations/{organisation_id}",
    response_model=OrganisationReadDTO,
)
async def get_organisation(organisation_id: int) -> OrganisationReadDTO:
    """Retrieve a specific organisation by its name.

    :param int organisation_id: The ID of the organisation to retrieve.
    :raises HTTPException: If the organisation is not found.
    :return OrganisationReadDTO: The requested organisation.
    """
    try:
        org = organisation_service.get(organisation_id)
    except ValidationError as e:
        _LOGGER.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        _LOGGER.error(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if org is None:
        msg = f"Organisation not found: {organisation_id}"
        _LOGGER.error(msg)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=msg,
        )
    return org


@organisations_router.post(
    "/organisations",
    response_model=int,
    status_code=status.HTTP_201_CREATED,
)
async def create_organisation(new_organisation: OrganisationCreateDTO) -> int:
    """
    Create an organisation.

    :param OrganisationCreateDTO new_organisation: The data of the organisation to be created.
    :raises HTTPException: If the organisation could not be created.
    :return int: The id of the newly created organisation.
    """
    try:
        created_org_id = organisation_service.create(new_organisation)
        return created_org_id

    except RepositoryError as e:
        _LOGGER.error(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except Exception as e:
        _LOGGER.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@organisations_router.put(
    "/organisations/{id}",
    response_model=OrganisationReadDTO,
)
async def update_organisation(
    id: int, updated_organisation: OrganisationWriteDTO
) -> OrganisationReadDTO:
    """
    Update an organisation.

    :param OrganisationWriteDTO updated_organisation: The organisation data to be updated.
    :param int id: The id of the organisation to be updated.
    :raises HTTPException: If the organisation could not be updated.
    :return OrganisationReadDTO: The updated organisation.
    """
    try:
        updated_org = organisation_service.update(id, updated_organisation)

    except RepositoryError as e:
        _LOGGER.error(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )
    except Exception as e:
        _LOGGER.error(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
    if updated_org is None:
        detail = f"Unable to find collection to update for id: {id}"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return updated_org
