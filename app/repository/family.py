"""Operations on the repository for the Family entity."""

import logging
import os
from datetime import datetime
from typing import Optional, Tuple, Union, cast

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
from sqlalchemy import desc, func, text
from sqlalchemy import update as db_update
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session, lazyload
from sqlalchemy.sql import Subquery
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

FamilyGeoMetaOrg = Tuple[
    Family,
    list[str],
    FamilyMetadata,
    Corpus,
    Organisation,
]


def get_family_geography_subquery(db: Session) -> Subquery:
    """
    Creates a subquery to aggregate geography values for families, accomodating
    those with multiple associated geographies.

    :param db Session: the database connection
    :return Query: A subquery containing family import IDs and their associated geography values
    """
    return (
        db.query(
            FamilyGeography.family_import_id,
            func.array_agg(Geography.value).label("geography_values"),
        )
        .join(Geography, Geography.id == FamilyGeography.geography_id)
        .group_by(FamilyGeography.family_import_id)
        .subquery()
    )


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.

    geography_subquery = get_family_geography_subquery(db)

    empty_array = sqlalchemy.cast([], ARRAY(String))

    query = (
        db.query(
            Family,
            func.coalesce(geography_subquery.c.geography_values, empty_array).label(
                "geography_values"
            ),
            FamilyMetadata,
            Corpus,
            Organisation,
        )
        .outerjoin(
            geography_subquery,
            geography_subquery.c.family_import_id == Family.import_id,
        )
        .join(FamilyMetadata, FamilyMetadata.family_import_id == Family.import_id)
        .join(FamilyCorpus, FamilyCorpus.family_import_id == Family.import_id)
        .join(Corpus, Corpus.import_id == FamilyCorpus.corpus_import_id)
        .join(Organisation, Corpus.organisation_id == Organisation.id)
        .group_by(
            Family.import_id,
            Family.title,
            geography_subquery.c.geography_values,
            FamilyMetadata.family_import_id,
            Corpus.import_id,
            Organisation,
        )
        .options(lazyload("*"))
    )
    return query


def _family_to_dto_search_endpoint(db: Session, family_row: dict) -> FamilyReadDTO:
    family_import_id = family_row["family_import_id"]
    metadata = cast(dict, family_row["value"])
    org = cast(str, family_row["name"])
    family_slugs = family_row["slugs"]
    event_ids = family_row["event_ids"] if family_row["event_ids"] else []
    document_ids = family_row["document_ids"] if family_row["document_ids"] else []
    collection_ids = (
        family_row["collection_ids"] if family_row["collection_ids"] else []
    )

    return FamilyReadDTO(
        import_id=str(family_import_id),
        title=str(family_row["family_title"]),
        summary=str(family_row["description"]),
        geography=str(
            family_row["geography_values"][0] if family_row["geography_values"] else ""
        ),
        geographies=[str(value) for value in family_row["geography_values"]],
        category=str(family_row["family_category"]),
        status=str(family_row["family_status"]),
        metadata=metadata,
        slug=str(family_slugs[0] if len(family_slugs) > 0 else ""),
        events=event_ids,
        published_date=family_row["published_date"],
        last_updated_date=family_row["last_updated_date"],
        documents=document_ids,
        collections=collection_ids,
        organisation=org,
        corpus_import_id=family_row["corpus_import_id"],
        corpus_title=cast(str, family_row["title"]),
        corpus_type=cast(str, family_row["corpus_type_name"]),
        created=cast(datetime, family_row["created"]),
        last_modified=cast(datetime, family_row["last_modified"]),
    )


def _family_to_dto(
    db: Session, fam_geo_meta_corp_org: FamilyGeoMetaOrg
) -> FamilyReadDTO:
    (
        fam,
        geo_values,
        meta,
        corpus,
        org,
    ) = fam_geo_meta_corp_org

    metadata = cast(dict, meta.value)
    org = cast(str, org.name)

    return FamilyReadDTO(
        import_id=str(fam.import_id),
        title=str(fam.title),
        summary=str(fam.description),
        geography=str(geo_values[0]) if geo_values else None,
        geographies=[str(value) for value in geo_values],
        category=str(fam.family_category),
        status=str(fam.family_status),
        metadata=metadata,
        slug=str(fam.slugs[0].name if len(fam.slugs) > 0 else ""),
        events=[str(e.import_id) for e in fam.events],
        published_date=fam.published_date,
        last_updated_date=fam.last_updated_date,
        documents=[str(d.import_id) for d in fam.family_documents],
        collections=[
            c.collection_import_id
            for c in db.query(CollectionFamily).filter(
                fam.import_id == CollectionFamily.family_import_id
            )
        ],
        organisation=org,
        corpus_import_id=cast(str, corpus.import_id),
        corpus_title=cast(str, corpus.title),
        corpus_type=cast(str, corpus.corpus_type_name),
        created=cast(datetime, fam.created),
        last_modified=cast(datetime, fam.last_modified),
        concepts=(
            [cast(dict, concepts) for concepts in fam.concepts] if fam.concepts else []
        ),
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
    """
    Returns all the families.

    :param db Session: the database connection
    :param org_id int: the ID of the organisation the user belongs to
    :return Optional[FamilyResponse]: All of things
    """
    query = _get_query(db)
    if org_id is not None:
        query = query.filter(Organisation.id == org_id)
    family_geo_metas = query.order_by(desc(Family.last_modified)).all()

    if not family_geo_metas:
        return []

    result = [_family_to_dto(db, fgm) for fgm in family_geo_metas]

    return result


def get(db: Session, import_id: str) -> Optional[FamilyReadDTO]:
    """
    Gets a single family from the repository.

    :param db Session: the database connection
    :param str import_id: The import_id of the family
    :return Optional[FamilyResponse]: A single family or nothing
    """
    try:
        fam_geo_meta = _get_query(db).filter(Family.import_id == import_id).one()
    except NoResultFound as e:
        _LOGGER.debug(e)
        return

    return _family_to_dto(db, fam_geo_meta)


def search(
    db: Session,
    search_params: dict[str, Union[str, int]],
    org_id: Optional[int],
    geography: Optional[list[str]],
) -> list[FamilyReadDTO]:
    """
    Gets a list of families from the repository searching given fields.

    :param db Session: the database connection
    :param dict search_params: Any search terms to filter on specified
        fields (title & summary by default if 'q' specified).
    :param org_id Optional[int]: the ID of the organisation the user belongs to
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

    results = [_family_to_dto_search_endpoint(db, row) for row in query_results]

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

    # Update basic fields
    if update_basics:
        updates = 0
        result = db.execute(
            db_update(Family)
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
            db_update(FamilyMetadata)
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
        for col in cols_to_remove:
            result = db.execute(
                db_delete(CollectionFamily).where(
                    CollectionFamily.collection_import_id == col
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
        query = _get_query(db)
        if org_id is not None:
            query = query.filter(Organisation.id == org_id)
        n_families = query.count()
    except NoResultFound as e:
        _LOGGER.debug(e)
        return

    return n_families


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
                db_delete(FamilyGeography).where(
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
        db.query(
            FamilyGeography.family_import_id,
        )
        .join(Geography, Geography.id == FamilyGeography.geography_id)
        .filter(Geography.display_value.in_(geographies))
    )
