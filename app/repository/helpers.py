"""Helper functions for repos"""

from typing import Optional, Union, cast
from uuid import uuid4

from db_client.models.dfce.family import Slug
from db_client.models.organisation.counters import CountedEntity, EntityCounter
from db_client.models.organisation.users import Organisation
from slugify import slugify
from sqlalchemy.orm import Session


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
