"""Helper functions for repos"""

from typing import cast
from uuid import uuid4
from slugify import slugify
from sqlalchemy.orm import Session

from app.clients.db.models.law_policy.family import Slug


def generate_slug(
    db: Session,
    title: str,
    attempts: int = 100,
    suffix_length: int = 4,
) -> str:
    """
    Generates a slug that doesn't already exists.

    :param Session db: The connection to the db
    :param str title: The title or name of the object you wish to slugify
    :param int attempts: The number of attempt to generate a unique slug before
    failing, defaults to 100
    :param int suffix_length: The suffix to produce uniqueness, defaults to 4
    :raises RuntimeError: If we cannot produce a unique slug
    :return str: the slug generated
    """
    lookup = set([cast(str, n) for n in db.query(Slug.name).all()])
    base = slugify(str(title))

    # TODO: try to extend suffix length if attempts are exhausted
    suffix = str(uuid4())[:suffix_length]
    count = 0
    while (slug := f"{base}_{suffix}") in lookup:
        count += 1
        suffix = str(uuid4())[:suffix_length]
        if count > attempts:
            raise RuntimeError(
                f"Failed to generate a slug for {base} after {attempts} attempts."
            )
    lookup.add(slug)
    return slug
