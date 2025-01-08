"""Helper functions for repos"""

import logging
from typing import Optional, Union, cast
from uuid import uuid4

from db_client.models.dfce.family import FamilyGeography, Slug
from db_client.models.organisation.counters import CountedEntity, EntityCounter
from db_client.models.organisation.users import Organisation
from slugify import slugify
from sqlalchemy import delete as db_delete
from sqlalchemy.orm import Session

from app.errors import RepositoryError

_LOGGER = logging.getLogger(__name__)


def generate_unique_slug(
    existing_slugs: set[str], title: str, attempts: int = 100, suffix_length: int = 6
) -> str:
    """
    Generates a slug that doesn't already exist.

    :param set[str] existing_slugs: A set of already existing slugs to validate against.
    :param str title: The title or name of the object you wish to slugify.
    :param int attempts: The number of attempt to generate a unique slug before
    failing, defaults to 100.
    :param int suffix_length: The suffix to produce uniqueness, defaults to 6.
    :raises RuntimeError: If we cannot produce a unique slug.
    :return str: The slug generated.
    """
    base = slugify(str(title))

    # TODO: try to extend suffix length if attempts are exhausted
    suffix = str(uuid4())[:suffix_length]
    count = 0
    while (slug := f"{base}_{suffix}") in existing_slugs:
        count += 1
        suffix = str(uuid4())[:suffix_length]
        if count > attempts:
            raise RuntimeError(
                f"Failed to generate a slug for {base} after {attempts} attempts."
            )
    existing_slugs.add(slug)
    return slug


def generate_slug(
    db: Session,
    title: str,
    attempts: int = 100,
    suffix_length: int = 4,
    created_slugs: Optional[set[str]] = set(),
) -> str:
    """
    Generates a slug for a given title.

    :param Session db: The connection to the db
    :param str title: The title or name of the object you wish to slugify
    :param int attempts: The number of attempt to generate a unique slug before
    failing, defaults to 100
    :param int suffix_length: The suffix to produce uniqueness, defaults to 4
    :param Optional[set[str]] created_slugs: A set of slugs created in the context within which
    this function runs that have not yet been committed to the DB
    :return str: the slug generated
    """
    saved_slugs = set([cast(str, n) for n in db.query(Slug.name).all()])

    existing_slugs = created_slugs.union(saved_slugs) if created_slugs else saved_slugs

    return generate_unique_slug(existing_slugs, title, attempts, suffix_length)


def generate_import_id(
    db: Session, entity_type: CountedEntity, org: Union[str, int]
) -> str:
    """
    Generates an import_id given the parameters.

    If the org id is supplied the name is queried for to find the counter.

    :param Session db: the database session
    :param CountedEntity entity_type: the entity to be counted
    :param Union[str, int] org: the organisation id or name.
    :return str: the generated import_id
    """

    if isinstance(org, str):
        org_name = org
    else:
        org_name = (
            db.query(Organisation.name).filter(Organisation.id == org).scalar_subquery()
        )

    counter: EntityCounter = (
        db.query(EntityCounter).filter(EntityCounter.prefix == org_name).one()
    )
    return counter.create_import_id(entity_type)


def remove_old_geographies(
    db: Session, import_id: str, geo_ids: list[int], original_geographies: set[int]
):
    """
    Removes geographies that are no longer in geo_ids.

    This function compares the original set of geographies with the new geo_ids
    and removes the geographies that are no longer present.

    :param Session db: the database session
    :param str import_id: the family import ID for the geographies
    :param list[int] geo_ids: the list of geography IDs to be kept
    :param set[int] original_geographies: the set of original geography IDs to be compared
    :raises RepositoryError: if a geography removal fails
    """
    cols_to_remove = set(original_geographies) - set(geo_ids)
    for col in cols_to_remove:
        result = db.execute(
            db_delete(FamilyGeography).where(FamilyGeography.geography_id == col)
        )

        if result.rowcount == 0:  # type: ignore
            msg = f"Could not remove family {import_id} from geography {col}"
            _LOGGER.error(msg)
            raise RepositoryError(msg)


def add_new_geographies(
    db: Session, import_id: str, geo_ids: list[int], original_geographies: set[int]
):
    """
    Adds new geographies that are not already in the original geographies.

    This function identifies the geographies that need to be added (i.e., those
    that are in geo_ids but not in the original set) and adds them to the database.

    :param Session db: the database session
    :param str import_id: the family import ID for the geographies
    :param list[str] geo_ids: the list of geography IDs to be added
    :param set[str] original_geographies: the set of original geography IDs to be checked against
    """
    cols_to_add = set(geo_ids) - set(original_geographies)

    for col in cols_to_add:
        db.flush()
        new_geography = FamilyGeography(
            family_import_id=import_id,
            geography_id=col,
        )
        db.add(new_geography)


def perform_family_geographies_update(db: Session, import_id: str, geo_ids: list[int]):
    """
    Updates geographies by removing old ones and adding new ones.

    This function performs a complete update by removing geographies that are no
    longer in geo_ids and adding new geographies that were not previously present.

    :param Session db: the database session
    :param str import_id: the family import ID for the geographies
    :param list[str] geo_ids: the list of geography IDs to be updated
    """
    original_geographies = set(
        [
            fg.geography_id
            for fg in db.query(FamilyGeography).filter(
                FamilyGeography.family_import_id == import_id
            )
        ]
    )

    remove_old_geographies(db, import_id, geo_ids, original_geographies)
    add_new_geographies(db, import_id, geo_ids, original_geographies)
