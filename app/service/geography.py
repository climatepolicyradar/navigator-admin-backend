from sqlalchemy.orm import Session

from app.errors import ValidationError
from app.repository import geography_repo


def get_id(db: Session, geo_string: str) -> int:
    """
    Fetch the ID of a geography and validate its existence.

    :param Session db: Database session.
    :param str geo_string: The geography iso value to look up.
    :raises ValidationError: If the geography value is invalid.
    :return int: The ID of the geography.
    """
    id = geography_repo.get_id_from_value(db, geo_string)
    if id is None:
        raise ValidationError(f"The geography value {geo_string} is invalid!")
    return id


def get_ids(db: Session, geo_strings: list[str]) -> list[int]:
    """
    Fetch IDs for multiple geographies and validate their existence.

    :param Session db: Database session.
    :param list[str] geo_strings: A list of geography iso values to look up.
    :raises ValidationError: If any of the geography values are invalid.
    :return list[int]: A list of IDs corresponding to the provided geography values.
    """

    geo_ids = geography_repo.get_ids_from_values(db, geo_strings)

    if len(geo_ids) != len(geo_strings):
        raise ValidationError(
            f"One or more of the following geography values are invalid: {', '.join(geo_strings)}"
        )

    return geo_ids
