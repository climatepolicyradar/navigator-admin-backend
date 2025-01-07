from typing import Optional

from db_client.models.dfce.geography import Geography
from sqlalchemy.orm import Session


def get_id_from_value(db: Session, geo_string: str) -> Optional[int]:
    """
    Fetch the ID of a geography based on its iso value.

    :param Session db: Database session.
    :param str geo_string: The geography value to look up.
    :return Optional[int]: The ID of the geography if found, otherwise None.
    """
    return db.query(Geography.id).filter_by(value=geo_string).scalar()


def get_ids_from_values(db: Session, geo_strings: list[str]) -> list[int]:
    """
    Fetch IDs for multiple geographies based on their iso values.

    :param Session db: Database session.
    :param list[str] geo_strings: A list of geography iso values to look up.
    :return list[int]: A list of IDs corresponding to the provided geography values.
    """
    return [
        geography.id
        for geography in db.query(Geography).filter(Geography.value.in_(geo_strings))
    ]
