"""Operations on the repository for the Family entity."""

import logging
from typing import Optional, Tuple, cast
from uuid import uuid4

from slugify import slugify
from app.db.models.app.users import Organisation
from app.db.models.law_policy.collection import CollectionFamily
from sqlalchemy.orm import Session
from app.db.models.law_policy.family import FamilyOrganisation, Slug
from app.db.models.law_policy.geography import Geography
from app.db.models.law_policy.metadata import FamilyMetadata
from app.errors.repository_error import RepositoryError
from app.model.family import FamilyDTO
from app.db.models.law_policy import Family
from sqlalchemy.exc import NoResultFound
from sqlalchemy_utils import escape_like
from sqlalchemy import or_, update as db_update, delete as db_delete
from sqlalchemy.orm import Query


_LOGGER = logging.getLogger(__name__)

FamilyGeoMetaOrg = Tuple[Family, Geography, FamilyMetadata, Organisation]


def _fam_geo_meta_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.
    return (
        db.query(Family, Geography, FamilyMetadata, Organisation)
        .join(Geography, Family.geography_id == Geography.id)
        .join(FamilyMetadata, FamilyMetadata.family_import_id == Family.import_id)
        .join(
            FamilyOrganisation, FamilyOrganisation.family_import_id == Family.import_id
        )
        .join(Organisation, FamilyOrganisation.organisation_id == Organisation.id)
    )


def _family_org_from_dto(
    dto: FamilyDTO, geo_id: int, org_id
) -> Tuple[Family, Organisation]:
    return (
        Family(
            import_id=dto.import_id,
            title=dto.title,
            description=dto.summary,
            geography_id=geo_id,
            family_category=dto.category,
        ),
        FamilyOrganisation(family_import_id=dto.import_id, organisation_id=org_id),
    )


def _family_to_dto(db: Session, fam_geo_meta_org: FamilyGeoMetaOrg) -> FamilyDTO:
    f = fam_geo_meta_org[0]
    geo_value = cast(str, fam_geo_meta_org[1].value)
    metadata = cast(dict, fam_geo_meta_org[2].value)
    org = cast(str, fam_geo_meta_org[3].name)
    return FamilyDTO(
        import_id=str(f.import_id),
        title=str(f.title),
        summary=str(f.description),
        geography=geo_value,
        category=str(f.family_category),
        status=str(f.family_status),
        metadata=metadata,
        slug=str(f.slugs[0].name if len(f.slugs) > 0 else ""),
        events=[str(e.import_id) for e in f.events],
        published_date=f.published_date,
        last_updated_date=f.last_updated_date,
        documents=[str(d.import_id) for d in f.family_documents],
        collections=[
            c.collection_import_id
            for c in db.query(CollectionFamily).filter(
                f.import_id == CollectionFamily.family_import_id
            )
        ],
        organisation=org,
    )


def _generate_slug(
    title: str,
    lookup: set[str],
    attempts: int = 100,
    suffix_length: int = 4,
):
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


def _update_intention(db, family, geo_id, original_family):
    update_title = cast(str, original_family.title) != family.title
    update_basics = (
        update_title
        or original_family.description != family.summary
        or original_family.geography_id != geo_id
        or original_family.family_category != family.category
    )
    existing_metadata = (
        db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == family.import_id)
        .one()
    )
    update_metadata = existing_metadata.value != family.metadata
    return update_title, update_basics, update_metadata


def all(db: Session) -> list[FamilyDTO]:
    """
    Returns all the families.

    :return Optional[FamilyResponse]: All of things
    """
    family_geo_metas = _fam_geo_meta_query(db).all()

    if not family_geo_metas:
        return []

    result = [_family_to_dto(db, fgm) for fgm in family_geo_metas]

    return result


def get(db: Session, import_id: str) -> Optional[FamilyDTO]:
    """
    Gets a single family from the repository.

    :param str import_id: The import_id of the family
    :return Optional[FamilyResponse]: A single family or nothing
    """
    try:
        fam_geo_meta = (
            _fam_geo_meta_query(db).filter(Family.import_id == import_id).one()
        )
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _family_to_dto(db, fam_geo_meta)


def search(db: Session, search_term: str) -> list[FamilyDTO]:
    """
    Gets a list of families from the repository searching title and summary.

    :param str search_term: Any search term to filter on title or summary
    :return Optional[list[FamilyResponse]]: A list of matches
    """
    term = f"%{escape_like(search_term)}%"
    search = or_(Family.title.ilike(term), Family.description.ilike(term))
    found = _fam_geo_meta_query(db).filter(search).all()

    return [_family_to_dto(db, f) for f in found]


def update(db: Session, family: FamilyDTO, geo_id: int) -> bool:
    """
    Updates a single entry with the new values passed.

    :param str import_id: The family import id to change.
    :param FamilyDTO family: The new values
    :param int geo_id: a validated geography id
    :return Optional[FamilyDTO]: The new values set or None if not found.
    """
    new_values = family.dict()

    original_family = (
        db.query(Family).filter(Family.import_id == family.import_id).one_or_none()
    )

    if original_family is None:  # Not found the family to update
        _LOGGER.error(f"Unable to find family for update {family}")
        return False

    # Now figure out the intention of the request:
    update_title, update_basics, update_metadata = _update_intention(
        db, family, geo_id, original_family
    )

    # Return if nothing to do
    if not update_title and not update_basics and not update_metadata:
        return True

    # Update basic fields
    if update_basics:
        result = db.execute(
            db_update(Family)
            .where(Family.import_id == family.import_id)
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
        # TODO: Validate metadata
        md_result = db.execute(
            db_update(FamilyMetadata)
            .where(FamilyMetadata.family_import_id == family.import_id)
            .values(value=family.metadata)
        )
        if md_result.rowcount == 0:  # type: ignore
            msg = (
                "Could not update the metadata for family: "
                + f"{family.import_id} to {family.metadata}"
            )
            _LOGGER.error(msg)
            raise RepositoryError(msg)

    # update slug if title changed
    if update_title:
        db.flush()
        lookup = set([cast(str, n) for n in db.query(Slug.name).all()])
        name = _generate_slug(family.title, lookup)
        new_slug = Slug(
            family_import_id=family.import_id,
            family_document_import_id=None,
            name=name,
        )
        db.add(new_slug)
        _LOGGER.info(f"Added a new slug for {family.import_id} of {new_slug.name}")

    return True


def create(
    db: Session, family: FamilyDTO, geo_id: int, org_id: int
) -> Optional[FamilyDTO]:
    """
    Creates a new family.

    :param FamilyDTO family: the values for the new family
    :param int geo_id: a validated geography id
    :return Optional[FamilyDTO]: the new family created
    """
    try:
        new_family, new_fam_org = _family_org_from_dto(family, geo_id, org_id)
        db.add(new_family)
        db.add(new_fam_org)
    except Exception as e:
        _LOGGER.error(e)
        return

    # Add a slug
    lookup = set([cast(str, n) for n in db.query(Slug.name).all()])
    db.add(
        Slug(
            family_import_id=family.import_id,
            family_document_import_id=None,
            name=_generate_slug(family.title, lookup),
        )
    )
    return family


def delete(db: Session, import_id: str) -> bool:
    """
    Deletes a single family by the import id.

    :param str import_id: The family import id to delete.
    :return bool: True if deleted False if not.
    """
    commands = [
        db_delete(FamilyOrganisation).where(
            FamilyOrganisation.family_import_id == import_id
        ),
        db_delete(FamilyMetadata).where(FamilyMetadata.family_import_id == import_id),
        db_delete(Family).where(Family.import_id == import_id),
    ]
    for c in commands:
        result = db.execute(c)

    return result.rowcount > 0  # type: ignore
