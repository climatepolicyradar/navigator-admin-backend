"""Operations on the repository for the Family entity.

This version removes ORM graph materialisation in read paths to avoid
n+1 loads and large session identity map growth. It uses projection only
SELECTs with SQL side aggregation for child collections and maps rows
directly to DTOs.
"""

import logging
import os
from datetime import datetime
from typing import Mapping, Optional, Union, cast

import sqlalchemy
from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import (
    Concept,
    DocumentStatus,
    Family,
    FamilyCorpus,
    FamilyDocument,
    FamilyEvent,
    FamilyGeography,
    FamilyStatus,
    Slug,
)
from db_client.models.dfce.geography import Geography
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.organisation.corpus import Corpus
from db_client.models.organisation.counters import CountedEntity
from db_client.models.organisation.users import Organisation
from sqlalchemy import Column, String
from sqlalchemy import delete as db_delete
from sqlalchemy import desc, func, select, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session
from sqlalchemy_utils import escape_like

from app.errors import RepositoryError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from app.repository.helpers import (
    construct_raw_sql_query_to_retrieve_all_families,
    generate_import_id,
    generate_slug,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def _get_query() -> sqlalchemy.sql.Select:
    """
    Build a projection-only SELECT for families with SQL-side aggregation of
    child collections. This avoids loading ORM graphs and eliminates N+1s.
    """
    # Aggregate geographies per family
    geo_subq = (
        select(
            FamilyGeography.family_import_id.label("fam_id"),
            func.array_agg(Geography.value).label("geography_values"),
        )
        .join(Geography, Geography.id == FamilyGeography.geography_id)
        .group_by(FamilyGeography.family_import_id)
        .subquery()
    )

    # Aggregate slugs per family
    # Get most recent slug per family (ordered by created desc, take first)
    # Use PostgreSQL-specific array_agg with ORDER BY clause
    slugs_subq = (
        select(
            Slug.family_import_id.label("fam_id"),
            func.array_agg(text("slug.name ORDER BY slug.created DESC")).label("slugs"),
        )
        .select_from(Slug)
        .group_by(Slug.family_import_id)
        .subquery()
    )

    # Aggregate events (import_ids) per family
    events_subq = (
        select(
            FamilyEvent.family_import_id.label("fam_id"),
            func.array_agg(FamilyEvent.import_id).label("event_ids"),
        )
        .group_by(FamilyEvent.family_import_id)
        .subquery()
    )

    # Aggregate documents (import_ids) per family
    docs_subq = (
        select(
            FamilyDocument.family_import_id.label("fam_id"),
            func.array_agg(FamilyDocument.import_id).label("document_ids"),
        )
        .group_by(FamilyDocument.family_import_id)
        .subquery()
    )

    # Aggregate collections (import_ids) per family
    cols_subq = (
        select(
            CollectionFamily.family_import_id.label("fam_id"),
            func.array_agg(CollectionFamily.collection_import_id).label(
                "collection_ids"
            ),
        )
        .group_by(CollectionFamily.family_import_id)
        .subquery()
    )

    # Calculate published_date: MIN(date) where event_type_name matches datetime_event_name
    # If no match found, fall back to MIN(date) of all events for that family
    matching_event_date = (
        select(func.min(FamilyEvent.date))
        .where(
            sqlalchemy.and_(
                FamilyEvent.family_import_id == Family.import_id,
                FamilyEvent.valid_metadata["datetime_event_name"][  # type: ignore
                    0
                ].astext.cast(  # type: ignore
                    sqlalchemy.Text
                )
                == FamilyEvent.event_type_name,
            )
        )
        .scalar_subquery()
    )

    fallback_min_date = (
        select(func.min(FamilyEvent.date))
        .where(FamilyEvent.family_import_id == Family.import_id)
        .scalar_subquery()
    )

    published_date_expr = func.coalesce(matching_event_date, fallback_min_date).label(
        "published_date"
    )

    # Calculate last_updated_date: MAX(date) where date <= current timestamp
    last_updated_date_expr = (
        select(func.max(FamilyEvent.date))
        .where(
            sqlalchemy.and_(
                FamilyEvent.family_import_id == Family.import_id,
                FamilyEvent.date <= func.current_timestamp(),
            )
        )
        .scalar_subquery()
        .label("last_updated_date")
    )

    # Calculate family_status based on document states
    family_status_expr = (
        sqlalchemy.case(
            (
                ~sqlalchemy.exists(
                    select(sqlalchemy.literal(1)).where(
                        FamilyDocument.family_import_id == Family.import_id
                    )
                ),
                sqlalchemy.literal(FamilyStatus.CREATED.value),
            ),
            else_=sqlalchemy.case(
                (
                    sqlalchemy.exists(
                        select(sqlalchemy.literal(1)).where(
                            sqlalchemy.and_(
                                FamilyDocument.family_import_id == Family.import_id,
                                FamilyDocument.document_status
                                == DocumentStatus.PUBLISHED,
                            )
                        )
                    ),
                    sqlalchemy.literal(FamilyStatus.PUBLISHED.value),
                ),
                else_=sqlalchemy.case(
                    (
                        sqlalchemy.exists(
                            select(sqlalchemy.literal(1)).where(
                                sqlalchemy.and_(
                                    FamilyDocument.family_import_id == Family.import_id,
                                    FamilyDocument.document_status
                                    == DocumentStatus.CREATED,
                                )
                            )
                        ),
                        sqlalchemy.literal(FamilyStatus.CREATED.value),
                    ),
                    else_=sqlalchemy.literal(FamilyStatus.DELETED.value),
                ),
            ),
        )
    ).label("family_status")

    empty_arr = func.cast([], ARRAY(String))

    # Base projection: only scalar columns + aggregated arrays
    stmt = (
        select(
            Family.import_id.label("import_id"),
            Family.title.label("family_title"),
            Family.description.label("description"),
            Family.family_category.label("family_category"),
            family_status_expr,
            published_date_expr,
            last_updated_date_expr,
            Family.created.label("created"),
            Family.last_modified.label("last_modified"),
            Family.concepts.label("concepts"),
            FamilyMetadata.value.label("metadata"),
            Corpus.import_id.label("corpus_import_id"),
            Corpus.title.label("corpus_title"),
            Corpus.corpus_type_name.label("corpus_type_name"),
            Organisation.name.label("organisation"),
            func.coalesce(geo_subq.c.geography_values, empty_arr).label(
                "geography_values"
            ),
            func.coalesce(slugs_subq.c.slugs, empty_arr).label("slugs"),
            func.coalesce(events_subq.c.event_ids, empty_arr).label("events"),
            func.coalesce(docs_subq.c.document_ids, empty_arr).label("documents"),
            func.coalesce(cols_subq.c.collection_ids, empty_arr).label("collections"),
        )
        .join(FamilyMetadata, FamilyMetadata.family_import_id == Family.import_id)
        .join(FamilyCorpus, FamilyCorpus.family_import_id == Family.import_id)
        .join(Corpus, Corpus.import_id == FamilyCorpus.corpus_import_id)
        .join(Organisation, Corpus.organisation_id == Organisation.id)
        .outerjoin(geo_subq, geo_subq.c.fam_id == Family.import_id)
        .outerjoin(slugs_subq, slugs_subq.c.fam_id == Family.import_id)
        .outerjoin(events_subq, events_subq.c.fam_id == Family.import_id)
        .outerjoin(docs_subq, docs_subq.c.fam_id == Family.import_id)
        .outerjoin(cols_subq, cols_subq.c.fam_id == Family.import_id)
        .group_by(
            Family.import_id,
            Family.title,
            Family.description,
            Family.family_category,
            Family.created,
            Family.last_modified,
            Family.concepts,
            FamilyMetadata.value,
            Corpus.import_id,
            Corpus.title,
            Corpus.corpus_type_name,
            Organisation.name,
            geo_subq.c.geography_values,
            slugs_subq.c.slugs,
            events_subq.c.event_ids,
            docs_subq.c.document_ids,
            cols_subq.c.collection_ids,
        )
    )
    return stmt


def _row_to_dto(row: Mapping) -> FamilyReadDTO:
    """
    Map a projected row (dict-like) into FamilyReadDTO without touching ORM objects.
    This keeps memory low and avoids holding references to ORM instances.
    """
    geos = [str(v) for v in (row["geography_values"] or [])]
    slugs = row["slugs"] or []
    concepts = row.get("concepts") or []
    return FamilyReadDTO(
        import_id=str(row["import_id"]),
        title=str(row["family_title"]),
        summary=str(row["description"]),
        geography=str(geos[0]) if geos else None,
        geographies=geos,
        category=str(row["family_category"]),
        status=str(row["family_status"]),
        metadata=cast(dict, row["metadata"]),
        slug=str(slugs[0]) if slugs else "",
        events=[str(e) for e in (row["events"] or [])],
        published_date=row["published_date"],
        last_updated_date=row["last_updated_date"],
        documents=[str(d) for d in (row["documents"] or [])],
        collections=[str(c) for c in (row["collections"] or [])],
        organisation=str(row["organisation"]),
        corpus_import_id=str(row["corpus_import_id"]),
        corpus_title=str(row["corpus_title"]),
        corpus_type=str(row["corpus_type_name"]),
        created=cast(datetime, row["created"]),
        last_modified=cast(datetime, row["last_modified"]),
        concepts=concepts,
    )


def _update_intention(
    db: Session,
    import_id: str,
    family: FamilyWriteDTO,
    geo_ids: list[int],
    original_family: Family,
):
    original_collections = [
        c.collection_import_id
        for c in db.query(CollectionFamily).filter(
            original_family.import_id == CollectionFamily.family_import_id
        )
    ]
    update_collections = set(original_collections) != set(family.collections)
    update_title = cast(str, original_family.title) != family.title

    current_family_geographies_ids = [
        family_geography.geography_id
        for family_geography in db.query(FamilyGeography).filter(
            FamilyGeography.family_import_id == import_id
        )
    ]
    update_geographies = set(current_family_geographies_ids) != set(geo_ids)

    update_basics = (
        update_title
        or original_family.description != family.summary
        or original_family.family_category != family.category
        or original_family.concepts != family.concepts
    )

    existing_metadata = (
        db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == import_id)
        .one()
    )
    update_metadata = existing_metadata.value != family.metadata
    return (
        update_title,
        update_basics,
        update_metadata,
        update_collections,
        update_geographies,
    )


def all(db: Session, org_id: Optional[int]) -> list[FamilyReadDTO]:
    """Return all families.

    Returns all the families as DTOs with a projection only query.
    Avoids loading ORM graphs and eliminates N+1 queries.

    :param db Session: the database connection
    :param org_id int: the ID of the organisation the user belongs to
    :return Optional[FamilyResponse]: All of things
    """
    stmt = _get_query()
    if org_id is not None:
        stmt = stmt.where(Organisation.id == org_id)
    rows = db.execute(stmt.order_by(desc(Family.last_modified))).mappings().fetchall()
    return [_row_to_dto(r) for r in rows]


def get(db: Session, import_id: str) -> Optional[FamilyReadDTO]:
    """Get a single family from the repository.

    Get a single family as DTO using projection only query.

    :param db Session: the database connection
    :param str import_id: The import_id of the family
    :return Optional[FamilyResponse]: A single family or nothing
    """
    stmt = _get_query().where(Family.import_id == import_id)
    row = db.execute(stmt).mappings().one_or_none()
    return _row_to_dto(row) if row else None


def search(
    db: Session,
    search_params: dict[str, Union[str, int]],
    org_id: Optional[int],
    geography: Optional[list[str]],
    corpus: Optional[list[str]] = None,
) -> list[FamilyReadDTO]:
    """
    Gets a list of families from the repository searching given fields.

    Search families via existing raw SQL builder (already projection
    like), then map rows to DTO without touching ORM relationships.

    :param db Session: the database connection
    :param dict search_params: Any search terms to filter on specified
        fields (title & summary by default if 'q' specified).
    :param org_id Optional[int]: the ID of the organisation the user belongs to
    :param geography Optional[list[str]]: geographies to filter on
    :param corpus Optional[list[str]]: corpus import IDs to filter on
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[FamilyReadDTO]: A list of families matching the search
        terms.
    """

    conditions = []
    params: dict[str, Union[str, int, list[str]]] = {
        "max_results": search_params["max_results"]
    }
    # We know that max_results will always have a value, so can set this when initialising, see query_params.py

    # Add conditions based on parameters
    if "q" in search_params:
        term = f"%{escape_like(search_params['q'])}%"
        conditions.append("(f.title ILIKE :q OR f.description ILIKE :q)")
        params["q"] = term
    else:
        if "title" in search_params:
            term = f"%{escape_like(search_params['title'])}%"
            conditions.append("f.title ILIKE :title")
            params["title"] = term

        if "summary" in search_params:
            term = f"%{escape_like(search_params['summary'])}%"
            conditions.append("f.description ILIKE :summary")
            params["summary"] = term

    if geography is not None:
        family_geographies = _get_family_geographies_by_display_values(db, geography)
        if family_geographies:
            conditions.append("f.import_id = ANY(:import_ids_for_geographies)")
            params["import_ids_for_geographies"] = [
                str(geography.family_import_id) for geography in family_geographies
            ]

    if corpus is not None:
        conditions.append("c.import_id = ANY(:import_ids_for_corpus)")
        params["import_ids_for_corpus"] = corpus

    if "status" in search_params:
        term = cast(str, search_params["status"]).upper()
        conditions.append(
            """
            CASE
                WHEN EXISTS (SELECT 1 FROM family_document fd WHERE fd.family_import_id = f.import_id AND fd.document_status = 'PUBLISHED') THEN 'PUBLISHED'
                WHEN EXISTS (SELECT 1 FROM family_document fd WHERE fd.family_import_id = f.import_id AND fd.document_status = 'CREATED') THEN 'CREATED'
                ELSE 'DELETED'
            END = :family_status
        """
        )
        params["family_status"] = term

    # Combine conditions into a WHERE clause
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    sql_query, query_params = construct_raw_sql_query_to_retrieve_all_families(
        params,
        org_id=org_id,
        filters=where_clause,
    )

    try:
        query = db.execute(text(sql_query), query_params)
        query_results = query.mappings().fetchall()

    except OperationalError as e:
        if "canceling statement due to statement timeout" in str(e):
            raise TimeoutError
        raise RepositoryError(e)

    # Build DTOs from projected rows (no ORM traversal)
    results: list[FamilyReadDTO] = []
    for row in query_results:
        # Row keys must match _row_to_dto expectations; raw SQL builder already
        # returns projected columns and arrays. Map by name.
        dto = FamilyReadDTO(
            import_id=str(row["family_import_id"]),
            title=str(row["family_title"]),
            summary=str(row["description"]),
            geography=str(
                row["geography_values"][0] if row["geography_values"] else ""
            ),
            geographies=[str(value) for value in (row["geography_values"] or [])],
            category=str(row["family_category"]),
            status=str(row["family_status"]),
            metadata=cast(dict, row["value"]),
            slug=str(row["slugs"][0]) if row.get("slugs") else "",
            events=[str(e) for e in (row.get("event_ids") or [])],
            published_date=row["published_date"],
            last_updated_date=row["last_updated_date"],
            documents=[str(d) for d in (row.get("document_ids") or [])],
            collections=[str(c) for c in (row.get("collection_ids") or [])],
            organisation=str(row["name"]),
            corpus_import_id=str(row["corpus_import_id"]),
            corpus_title=str(row["title"]),
            corpus_type=str(row["corpus_type_name"]),
            created=cast(datetime, row["created"]),
            last_modified=cast(datetime, row["last_modified"]),
            concepts=[],  # intentionally excluded for search results too
        )
        results.append(dto)
    return results


def update(
    db: Session, import_id: str, family: FamilyWriteDTO, geo_ids: list[int]
) -> bool:
    """
    Updates a single entry with the new values passed.

    :param db Session: the database connection
    :param str import_id: The family import id to change.
    :param FamilyDTO family: The new values
    :param int geo_id: a validated geography id
    :param list[int] geo_ids: a list of validated geography ids
    :return bool: True if new values were set otherwise false.
    """
    new_values = family.model_dump()

    original_family = (
        db.query(Family).filter(Family.import_id == import_id).one_or_none()
    )

    if original_family is None:
        _LOGGER.error(f"Unable to find family for update {family}")
        return False

    # Now figure out the intention of the request:
    (
        update_title,
        update_basics,
        update_metadata,
        update_collections,
        update_geographies,
    ) = _update_intention(db, import_id, family, geo_ids, original_family)

    # Return if nothing to do
    if not (
        update_title
        or update_basics
        or update_metadata
        or update_collections
        or update_geographies
    ):
        return True

    if update_basics:
        updates = 0
        result = db.execute(
            sqlalchemy.update(Family)
            .where(Family.import_id == import_id)
            .values(
                title=new_values["title"],
                description=new_values["summary"],
                family_category=new_values["category"],
                concepts=new_values["concepts"],
            )
        )

        updates += result.rowcount  # type: ignore
        if updates == 0:  # type: ignore
            msg = f"Could not update family fields: {family}"
            _LOGGER.error(msg)
            raise RepositoryError(msg)

    # Update if metadata is changed
    if update_metadata:
        md_result = db.execute(
            sqlalchemy.update(FamilyMetadata)
            .where(FamilyMetadata.family_import_id == import_id)
            .values(value=family.metadata)
        )
        if md_result.rowcount == 0:  # type: ignore
            msg = (
                "Could not update the metadata for family: "
                + f"{import_id} to {family.metadata}"
            )
            _LOGGER.error(msg)
            raise RepositoryError(msg)

    # Update slug if title changed
    if update_title:
        db.flush()
        name = generate_slug(db, family.title)
        new_slug = Slug(
            family_import_id=import_id,
            family_document_import_id=None,
            name=name,
        )
        db.add(new_slug)
        _LOGGER.info(f"Added a new slug for {import_id} of {new_slug.name}")

    # Update collections if collections changed.
    if update_collections:
        original_collections = set(
            [
                c.collection_import_id
                for c in db.query(CollectionFamily).filter(
                    original_family.import_id == CollectionFamily.family_import_id
                )
            ]
        )

        # Remove any collections that were originally associated with the family but
        # now aren't.
        cols_to_remove = set(original_collections) - set(family.collections)
        print(f"cols_to_remove: {cols_to_remove}")
        for col in cols_to_remove:
            result = db.execute(
                sqlalchemy.delete(CollectionFamily).where(
                    CollectionFamily.collection_import_id == col
                    and CollectionFamily.family_import_id == import_id
                )
            )

            if result.rowcount == 0:  # type: ignore
                msg = f"Could not remove family {import_id} from collection {col}"
                _LOGGER.error(msg)
                raise RepositoryError(msg)

        # Add any collections that weren't originally associated with the family.
        cols_to_add = set(family.collections) - set(original_collections)
        for col in cols_to_add:
            db.flush()
            new_collection = CollectionFamily(
                family_import_id=import_id,
                collection_import_id=col,
            )
            db.add(new_collection)

    # Update geographies if geographies have changed.
    if update_geographies:
        perform_family_geographies_update(db, import_id, geo_ids)

    return True


def create(
    db: Session, family: FamilyCreateDTO, geo_ids: list[int], org_id: int
) -> str:
    """
    Creates a new family.

    :param db Session: the database connection
    :param FamilyDTO family: the values for the new family
    :param int geo_id: a validated geography id
    :param int org_id: a validated organisation id
    :return str: The ID of the created family.
    """
    try:
        import_id = family.import_id or cast(
            Column,
            generate_import_id(db, CountedEntity.Family, org_id),
        )
        new_family = Family(
            import_id=import_id,
            title=family.title,
            description=family.summary,
            family_category=family.category,
            concepts=[Concept(**c) for c in (family.concepts or [])],
        )
        db.add(new_family)

        family_geographies = [
            FamilyGeography(family_import_id=import_id, geography_id=geo_id)
            for geo_id in geo_ids
        ]
        db.add_all(family_geographies)

        # Add corpus - family link.
        db.add(
            FamilyCorpus(
                family_import_id=new_family.import_id,
                corpus_import_id=family.corpus_import_id,
            )
        )

        db.flush()
    except Exception as e:
        _LOGGER.exception(f"Error trying to create Family: {e}")
        raise RepositoryError(e)

    # Add a slug
    db.add(
        Slug(
            family_import_id=new_family.import_id,
            family_document_import_id=None,
            name=generate_slug(db, family.title),
        )
    )
    db.flush()

    # Add the metadata
    db.add(
        FamilyMetadata(
            family_import_id=new_family.import_id,
            value=family.metadata,
        )
    )
    db.flush()

    # Add any collections.
    for col in set(family.collections):
        new_collection = CollectionFamily(
            family_import_id=new_family.import_id,
            collection_import_id=col,
        )
        db.add(new_collection)
    return cast(str, new_family.import_id)


def hard_delete(db: Session, import_id: str):
    """Forces a hard delete of the family.

    :param db Session: the database connection
    :param str import_id: The family import id to delete.
    :return bool: True if deleted False if not.
    """
    commands = [
        db_delete(CollectionFamily).where(
            CollectionFamily.family_import_id == import_id
        ),
        db_delete(FamilyEvent).where(FamilyEvent.family_import_id == import_id),
        db_delete(FamilyCorpus).where(FamilyCorpus.family_import_id == import_id),
        db_delete(Slug).where(Slug.family_import_id == import_id),
        db_delete(FamilyMetadata).where(FamilyMetadata.family_import_id == import_id),
        db_delete(FamilyGeography).where(FamilyGeography.family_import_id == import_id),
        db_delete(Family).where(Family.import_id == import_id),
    ]

    for c in commands:
        result = db.execute(c)
        # Keep this for debug.
        _LOGGER.debug("%s, %s", str(c), result.rowcount)  # type: ignore

    fam_deleted = db.query(Family).filter(Family.import_id == import_id).one_or_none()
    if fam_deleted is not None:
        msg = f"Could not hard delete family: {import_id}"
        _LOGGER.error(msg)

    return bool(fam_deleted is None)


def delete(db: Session, import_id: str) -> bool:
    """
    Deletes a single family by the import id.

    :param db Session: the database connection
    :param str import_id: The family import id to delete.
    :return bool: True if deleted False if not.
    """
    found = db.query(Family).filter(Family.import_id == import_id).one_or_none()
    if found is None:
        return False

    # Only perform if we have docs associated with this family
    family_docs = (
        db.query(FamilyDocument)
        .filter(FamilyDocument.family_import_id == import_id)
        .all()
    )

    if len(family_docs) == 0 and found.family_status == FamilyStatus.CREATED:
        return hard_delete(db, import_id)

    # Soft delete all documents associated with the family.
    for doc in family_docs:
        doc.document_status = DocumentStatus.DELETED
        db.add(doc)

    # Check family has been soft deleted if all documents have also been soft deleted.
    fam_deleted = db.query(Family).filter(Family.import_id == import_id).one()
    if fam_deleted.family_status != FamilyStatus.DELETED:  # type: ignore
        msg = f"Could not soft delete family: {import_id}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    return bool(fam_deleted.family_status == FamilyStatus.DELETED)


def get_organisation(db: Session, family_import_id: str) -> Optional[Organisation]:
    """
    Gets the owning organisation of a family.

    :param db Session: the database connection
    :param str family_import_id: The family import_id in question
    :return Optional[Organisation]: Any associated organisation
    """

    return (
        db.query(Organisation)
        .join(Corpus, Corpus.organisation_id == Organisation.id)
        .join(FamilyCorpus, FamilyCorpus.corpus_import_id == Corpus.import_id)
        .filter(FamilyCorpus.family_import_id == family_import_id)
        .group_by(Organisation.id)
        .one_or_none()
    )


def count(db: Session, org_id: Optional[int]) -> Optional[int]:
    """
    Counts the number of families in the repository.

    :param db Session: the database connection
    :param org_id int: the ID of the organisation the user belongs to
    :return Optional[int]: The number of families in the repository or none.
    """
    try:
        stmt = _get_query()
        if org_id is not None:
            stmt = stmt.where(Organisation.id == org_id)
        n_families = db.execute(select(func.count()).select_from(stmt)).scalar()
    except NoResultFound as e:
        _LOGGER.debug(e)
        return

    return n_families if n_families is not None else 0


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
        try:
            db.execute(
                sqlalchemy.delete(FamilyGeography).where(
                    FamilyGeography.geography_id == col,
                    FamilyGeography.family_import_id == import_id,
                )
            )
        except Exception as e:
            msg = f"Could not remove family {import_id} from geography {col}: {str(e)}"
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
    :raises RepositoryError: if fails to add a geography
    """
    cols_to_add = set(geo_ids) - set(original_geographies)

    for col in cols_to_add:
        try:
            new_geography = FamilyGeography(
                family_import_id=import_id,
                geography_id=col,
            )
            db.add(new_geography)
            db.flush()
        except Exception as e:
            msg = f"Failed to add geography {col} to family {import_id}: {str(e)}"
            _LOGGER.error(msg)
            raise RepositoryError(msg)


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


def _get_family_geographies_by_display_values(
    db: Session, geographies: list[str]
) -> Query:
    """
    Filters import IDs of families based on the provided geography values.
    :param db Session: the database connection
    :param list[str] geographies: A list of geography display values to filter by
    :return Query: A subquery containing the filtered family import IDs
    """

    return (
        db.query(FamilyGeography.family_import_id)
        .join(Geography, Geography.id == FamilyGeography.geography_id)
        .filter(Geography.display_value.in_(geographies))
    )
