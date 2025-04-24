"""Helper functions for repos"""

import logging
from functools import cache
from typing import Optional, Tuple, Union, cast
from uuid import uuid4

from db_client.models.dfce.family import Slug
from db_client.models.organisation.counters import CountedEntity, EntityCounter
from db_client.models.organisation.users import Organisation
from slugify import slugify
from sqlalchemy.orm import Session

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


@cache
def get_db_slugs(
    db: Session,
) -> set[str]:
    """
    Retrieves existing slugs for a family.

    :param Session db: The connection to the db.
    :return set[str]: The set of all slugs in the database.
    """
    return set([cast(str, n) for n in db.query(Slug.name).all()])


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
    saved_slugs = get_db_slugs(db)

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


def construct_raw_sql_query_to_retrieve_all_families(
    filter_params: dict[str, Union[str, int, list[str]]],
    org_id: Optional[int] = None,
    filters: Optional[str] = None,
) -> Tuple[str, dict[str, Union[str, int]]]:
    """
    Constructs a raw SQL query for retrieving family-related data based on provided filters.

    :param Optional[int] org_id: The ID of the organization to filter by (default is None).
    :param Optional[str] filters: A string representing additional filtering conditions (default is None).
    :param Optional[Dict[str, any]] filter_params: A dictionary of filter parameters to be used in the query (default is None).
    :return: A tuple containing the constructed SQL query string and a dictionary of query parameters.
    """
    main_sql_query = """
        SELECT
            f.*,
            f.title AS family_title,
            geography_subquery.geography_values,
            family_documents_subquery.document_ids,
            family_events_subquery.event_ids,
            fm.*,
            c.*,
            c.import_id AS corpus_import_id,
            o.*,
            slug_subquery.slugs,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM family_document fd
                WHERE fd.family_import_id = f.import_id
                AND fd.document_status = 'PUBLISHED'
            ) THEN 'PUBLISHED'
            WHEN EXISTS (
                SELECT 1
                FROM family_document fd
                WHERE fd.family_import_id = f.import_id
                AND fd.document_status = 'CREATED'
            ) THEN 'CREATED'
            ELSE 'DELETED'
        END AS family_status,
        (
            SELECT MAX(fe.date)
            FROM family_event fe
            WHERE fe.family_import_id = f.import_id
                AND fe.date <= CURRENT_TIMESTAMP
        ) AS last_updated_date,
        (
            SELECT MIN(fe.date)
            FROM family_event fe
            WHERE fe.family_import_id = f.import_id
            AND EXISTS (
                    SELECT 1
                    FROM jsonb_array_elements_text(fe.valid_metadata::jsonb->'datetime_event_name') AS datetime_event_name
                    WHERE datetime_event_name = fe.event_type_name
                )
        ) AS published_date
        FROM
            family f
        JOIN
            (
                SELECT
                    fg.family_import_id,
                    array_agg(g.value) AS geography_values
                FROM
                    family_geography fg
                JOIN
                    geography g ON g.id = fg.geography_id
                GROUP BY
                    fg.family_import_id
            ) AS geography_subquery
            ON geography_subquery.family_import_id = f.import_id
        LEFT JOIN
            (
                SELECT
                    fd.family_import_id,
                    array_agg(fd.import_id) AS document_ids
                FROM
                    family_document fd
                GROUP BY
                    fd.family_import_id
            ) AS family_documents_subquery
            ON family_documents_subquery.family_import_id = f.import_id
        LEFT JOIN
            (
                SELECT
                    fe.family_import_id,
                    array_agg(fe.import_id) AS event_ids
                FROM
                    family_event fe
                GROUP BY
                    fe.family_import_id
            ) AS family_events_subquery
            ON family_events_subquery.family_import_id = f.import_id
        LEFT JOIN
            (
                SELECT
                    s.family_import_id,
                    array_agg(s.name ORDER BY s.created) AS slugs  -- Aggregate slugs and order by `created`
                FROM
                    slug s
                GROUP BY
                    s.family_import_id
            ) AS slug_subquery
            ON slug_subquery.family_import_id = f.import_id
        JOIN
            family_metadata fm ON fm.family_import_id = f.import_id
        JOIN
            family_corpus fc ON fc.family_import_id = f.import_id
        JOIN
            corpus c ON c.import_id = fc.corpus_import_id
        JOIN
            organisation o ON o.id = c.organisation_id
        """

    where_conditions = []
    query_params = {}

    if org_id is not None:
        where_conditions.append("o.id = :org_id")
        query_params["org_id"] = org_id

    if filters:
        where_conditions.append(filters)
        if filter_params:
            query_params.update(filter_params)

    # Combine WHERE conditions
    if where_conditions:
        where_clause = " AND ".join(where_conditions)
        main_sql_query += f" WHERE {where_clause}"

    # Append GROUP BY at the end
    main_sql_query += """
    GROUP BY
        f.import_id, f.title, geography_subquery.geography_values,
        family_documents_subquery.document_ids, family_events_subquery.event_ids,
        fm.family_import_id, c.import_id, o.id, slug_subquery.slugs
    ORDER BY f.last_modified DESC
    LIMIT :max_results
    """

    return main_sql_query, query_params
