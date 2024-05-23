"""Operations on the repository for the Family entity."""

import logging
from datetime import datetime
from typing import Optional, Tuple, Union, cast

from db_client.models.dfce.collection import CollectionFamily
from db_client.models.dfce.family import (
    DocumentStatus,
    Family,
    FamilyCorpus,
    FamilyDocument,
    FamilyEvent,
    FamilyStatus,
    Slug,
)
from db_client.models.dfce.geography import Geography
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.organisation.corpus import Corpus
from db_client.models.organisation.counters import CountedEntity
from db_client.models.organisation.users import Organisation
from sqlalchemy import Column, and_
from sqlalchemy import delete as db_delete
from sqlalchemy import desc, or_
from sqlalchemy import update as db_update
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session
from sqlalchemy_utils import escape_like

from app.errors import RepositoryError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from app.repository.helpers import generate_import_id, generate_slug

_LOGGER = logging.getLogger(__name__)

FamilyGeoMetaOrg = Tuple[Family, Geography, FamilyMetadata, Corpus, Organisation]


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.
    return (
        db.query(Family, Geography, FamilyMetadata, Corpus, Organisation)
        .join(Geography, Family.geography_id == Geography.id)
        .join(FamilyMetadata, FamilyMetadata.family_import_id == Family.import_id)
        .join(FamilyCorpus, FamilyCorpus.family_import_id == Family.import_id)
        .join(Corpus, Corpus.import_id == FamilyCorpus.corpus_import_id)
        .join(Organisation, Corpus.organisation_id == Organisation.id)
    )


def _family_to_dto(
    db: Session, fam_geo_meta_corp_org: FamilyGeoMetaOrg
) -> FamilyReadDTO:
    fam, geo, meta, corpus, org = fam_geo_meta_corp_org

    geo_value = cast(str, geo.value)
    metadata = cast(dict, meta.value)
    org = cast(str, org.name)
    return FamilyReadDTO(
        import_id=str(fam.import_id),
        title=str(fam.title),
        summary=str(fam.description),
        geography=geo_value,
        category=str(fam.family_category),
        status=str(fam.family_status),
        metadata=metadata,
        slug=str(fam.slugs[-1].name if len(fam.slugs) > 0 else ""),
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
    )


def _update_intention(
    db: Session,
    import_id: str,
    family: FamilyWriteDTO,
    geo_id: int,
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
    update_basics = (
        update_title
        or original_family.description != family.summary
        or original_family.geography_id != geo_id
        or original_family.family_category != family.category
    )
    existing_metadata = (
        db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == import_id)
        .one()
    )
    update_metadata = existing_metadata.value != family.metadata
    return update_title, update_basics, update_metadata, update_collections


def all(db: Session, org_id: int, is_superuser: bool) -> list[FamilyReadDTO]:
    """
    Returns all the families.

    :param db Session: the database connection
    :return Optional[FamilyResponse]: All of things
    """
    if is_superuser:
        family_geo_metas = _get_query(db).order_by(desc(Family.last_modified)).all()
    else:
        family_geo_metas = (
            _get_query(db)
            .filter(Organisation.id == org_id)
            .order_by(desc(Family.last_modified))
            .all()
        )

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
        _LOGGER.error(e)
        return

    return _family_to_dto(db, fam_geo_meta)


def search(
    db: Session, query_params: dict[str, Union[str, int]]
) -> list[FamilyReadDTO]:
    """
    Gets a list of families from the repository searching given fields.

    :param db Session: the database connection
    :param dict query_params: Any search terms to filter on specified
        fields (title & summary by default if 'q' specified).
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[FamilyReadDTO]: A list of families matching the search
        terms.
    """
    search = []
    if "q" in query_params.keys():
        term = f"%{escape_like(query_params['q'])}%"
        search.append(or_(Family.title.ilike(term), Family.description.ilike(term)))
    else:
        if "title" in query_params.keys():
            term = f"%{escape_like(query_params['title'])}%"
            search.append(Family.title.ilike(term))

        if "summary" in query_params.keys():
            term = f"%{escape_like(query_params['summary'])}%"
            search.append(Family.description.ilike(term))

    if "geography" in query_params.keys():
        term = cast(str, query_params["geography"])
        search.append(
            or_(
                Geography.display_value == term.title(), Geography.value == term.upper()
            )
        )

    if "status" in query_params.keys():
        term = cast(str, query_params["status"])
        search.append(Family.family_status == term.capitalize())

    condition = and_(*search) if len(search) > 1 else search[0]
    try:
        found = (
            _get_query(db)
            .filter(condition)
            .order_by(desc(Family.last_modified))
            .limit(query_params["max_results"])
            .all()
        )
    except OperationalError as e:
        if "canceling statement due to statement timeout" in str(e):
            raise TimeoutError
        raise RepositoryError(e)

    return [_family_to_dto(db, f) for f in found]


def update(db: Session, import_id: str, family: FamilyWriteDTO, geo_id: int) -> bool:
    """
    Updates a single entry with the new values passed.

    :param db Session: the database connection
    :param str import_id: The family import id to change.
    :param FamilyDTO family: The new values
    :param int geo_id: a validated geography id
    :return bool: True if new values were set otherwise false.
    """
    new_values = family.model_dump()

    original_family = (
        db.query(Family).filter(Family.import_id == import_id).one_or_none()
    )

    if original_family is None:  # Not found the family to update
        _LOGGER.error(f"Unable to find family for update {family}")
        return False

    # Now figure out the intention of the request:
    (
        update_title,
        update_basics,
        update_metadata,
        update_collections,
    ) = _update_intention(db, import_id, family, geo_id, original_family)

    # Return if nothing to do
    if not (update_title or update_basics or update_metadata or update_collections):
        return True

    # Update basic fields
    if update_basics:
        result = db.execute(
            db_update(Family)
            .where(Family.import_id == import_id)
            .values(
                title=new_values["title"],
                description=new_values["summary"],
                geography_id=geo_id,
                family_category=new_values["category"],
            )
        )
        if result.rowcount == 0:  # type: ignore
            msg = "Could not update family fields: {family}"
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

    return True


def create(db: Session, family: FamilyCreateDTO, geo_id: int, org_id: int) -> str:
    """
    Creates a new family.

    :param db Session: the database connection
    :param FamilyDTO family: the values for the new family
    :param int geo_id: a validated geography id
    :param int org_id: a validated organisation id
    :return bool: True if new Family was created otherwise False.
    """
    try:
        import_id = cast(Column, generate_import_id(db, CountedEntity.Family, org_id))
        new_family = Family(
            import_id=import_id,
            title=family.title,
            description=family.summary,
            geography_id=geo_id,
            family_category=family.category,
        )
        db.add(new_family)

        # Add corpus - family link.
        db.add(
            FamilyCorpus(
                family_import_id=new_family.import_id,
                corpus_import_id=family.corpus_import_id,
            )
        )

        db.flush()
    except:
        _LOGGER.exception("Error trying to create Family")
        raise

    # Add a slug
    db.add(
        Slug(
            family_import_id=new_family.import_id,
            family_document_import_id=None,
            name=generate_slug(db, family.title),
        )
    )
    db.flush()

    # TODO Validate that the metadata being added conforms to corpus type. PDCT-945

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
    family_doc_count = (
        db.query(FamilyDocument)
        .filter(FamilyDocument.family_import_id == import_id)
        .count()
    )

    if family_doc_count > 0:
        # Soft delete all documents associated with the family.
        result = db.execute(
            db_update(FamilyDocument)
            .filter(FamilyDocument.family_import_id == import_id)
            .values(document_status=DocumentStatus.DELETED)
        )

        if result.rowcount == 0:  # type: ignore
            msg = f"Could not soft delete documents in family : {import_id}"
            _LOGGER.error(msg)
            raise RepositoryError(msg)

    elif family_doc_count == 0 and found.family_status == FamilyStatus.CREATED:
        commands = [
            db_delete(CollectionFamily).where(
                CollectionFamily.family_import_id == import_id
            ),
            db_delete(FamilyEvent).where(FamilyEvent.family_import_id == import_id),
            db_delete(FamilyCorpus).where(FamilyCorpus.family_import_id == import_id),
            db_delete(Slug).where(Slug.family_import_id == import_id),
            db_delete(FamilyMetadata).where(
                FamilyMetadata.family_import_id == import_id
            ),
            db_delete(Family).where(Family.import_id == import_id),
        ]

        for c in commands:
            result = db.execute(c)
            # Keep this for debug.
            _LOGGER.debug("%s, %s", str(c), result.rowcount)  # type: ignore
        db.commit()

        fam_deleted = (
            db.query(Family).filter(Family.import_id == import_id).one_or_none()
        )
        if fam_deleted is not None:
            msg = f"Could not hard delete family: {import_id}"
            _LOGGER.error(msg)

        return bool(fam_deleted is None)

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
        .one()
    )


def count(db: Session, org_id: int, is_superuser: bool) -> Optional[int]:
    """
    Counts the number of families in the repository.

    :param db Session: the database connection
    :param org_id int: the ID of the organisation the user belongs to
    :param is_superuser bool: whether the user is a superuser
    :return Optional[int]: The number of families in the repository or none.
    """
    try:
        if is_superuser:
            n_families = _get_query(db).count()
        else:
            n_families = _get_query(db).filter(Organisation.id == org_id).count()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return n_families
