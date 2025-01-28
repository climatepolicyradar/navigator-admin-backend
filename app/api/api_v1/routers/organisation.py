import logging
from typing import Union

from fastapi import APIRouter, HTTPException, status

from app.errors import RepositoryError, ValidationError
from app.model.organisation import OrganisationReadDTO
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )


@organisations_router.get(
    "/organisations/{organisation}",
    response_model=OrganisationReadDTO,
)
async def get_organisation(organisation: Union[int, str]) -> OrganisationReadDTO:
    """Retrieve a specific organisation by its name.

    :param Union[int, str] organisation: The ID or name of the
        organisation to retrieve.
    :raises HTTPException: If the organisation is not found.
    :return OrganisationReadDTO: The requested organisation.
    """
    try:
        org = organisation_service.get(organisation)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except RepositoryError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=e.message
        )

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organisation not found: {organisation}",
        )
    return org
