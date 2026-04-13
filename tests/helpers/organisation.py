"""Factories for organisation DTOs used in tests."""

from app.model.organisation import (
    OrganisationCreateDTO,
    OrganisationReadDTO,
    OrganisationWriteDTO,
)


def create_organisation_read_dto(
    id: int = 1,
    internal_name: str = "Acme Ltd",
    display_name: str = "Acme",
    description: str = "Widgets",
    org_type: str = "ORG",
    attribution_url: str | None = None,
) -> OrganisationReadDTO:
    """Build a read DTO with sensible defaults.

    :param id: Organisation primary key.
    :type id: int
    :param internal_name: Stable internal name.
    :type internal_name: str
    :param display_name: Human-facing name.
    :type display_name: str
    :param description: Description text.
    :type description: str
    :param org_type: Organisation type code.
    :type org_type: str
    :param attribution_url: Optional attribution URL.
    :type attribution_url: str | None
    :return: Configured read DTO.
    :rtype: OrganisationReadDTO
    """
    return OrganisationReadDTO(
        id=id,
        internal_name=internal_name,
        display_name=display_name,
        description=description,
        type=org_type,
        attribution_url=attribution_url,
    )


def create_organisation_create_dto(
    internal_name: str = "Acme Ltd",
    display_name: str = "Acme",
    description: str = "Widgets",
    org_type: str = "ORG",
    attribution_url: str | None = None,
) -> OrganisationCreateDTO:
    """Build a create DTO with sensible defaults.

    :param internal_name: Stable internal name.
    :type internal_name: str
    :param display_name: Human-facing name.
    :type display_name: str
    :param description: Description text.
    :type description: str
    :param org_type: Organisation type code.
    :type org_type: str
    :param attribution_url: Optional attribution URL.
    :type attribution_url: str | None
    :return: Configured create DTO.
    :rtype: OrganisationCreateDTO
    """
    return OrganisationCreateDTO(
        internal_name=internal_name,
        display_name=display_name,
        description=description,
        type=org_type,
        attribution_url=attribution_url,
    )


def create_organisation_write_dto(
    internal_name: str = "Acme Ltd",
    display_name: str = "Acme",
    description: str = "Widgets",
    org_type: str = "ORG",
    attribution_url: str | None = None,
) -> OrganisationWriteDTO:
    """Build a write DTO with sensible defaults.

    :param internal_name: Stable internal name.
    :type internal_name: str
    :param display_name: Human-facing name.
    :type display_name: str
    :param description: Description text.
    :type description: str
    :param org_type: Organisation type code.
    :type org_type: str
    :param attribution_url: Optional attribution URL.
    :type attribution_url: str | None
    :return: Configured write DTO.
    :rtype: OrganisationWriteDTO
    """
    return OrganisationWriteDTO(
        internal_name=internal_name,
        display_name=display_name,
        description=description,
        type=org_type,
        attribution_url=attribution_url,
    )
