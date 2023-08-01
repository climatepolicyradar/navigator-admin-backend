"""Operations on the repository for the Family entity."""

import logging
from typing import Optional, Tuple
from app.db.models.law_policy.collection import CollectionFamily
from sqlalchemy.orm import Session
from app.db.models.law_policy.family import FamilyOrganisation
from app.db.models.law_policy.geography import Geography
from app.db.models.law_policy.metadata import FamilyMetadata
from app.model.family import FamilyDTO
from app.db.models.law_policy import Family
from sqlalchemy.exc import NoResultFound
from sqlalchemy_utils import escape_like
from sqlalchemy import or_, update as db_update, delete as db_delete


_LOGGER = logging.getLogger(__name__)

FamilyGeoMeta = Tuple[Family, str, dict]


def _fam_geo_meta_query(db: Session):
    return (
        db.query(Family, Geography.value, FamilyMetadata.value)
        .join(Geography, Family.geography_id == Geography.id)
        .join(FamilyMetadata, FamilyMetadata.family_import_id == Family.import_id)
    )


def _family_from_dto(dto: FamilyDTO, geo_id: int) -> Family:
    return Family(
        import_id=dto.import_id,
        title=dto.title,
        description=dto.summary,
        geography_id=geo_id,
        family_category=dto.category,
    )


def _family_to_dto(db: Session, fam_geo_meta: FamilyGeoMeta) -> FamilyDTO:
    f = fam_geo_meta[0]
    geo_value = fam_geo_meta[1]
    metadata = fam_geo_meta[2]
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
    )


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


def update(db: Session, family: FamilyDTO, geo_id: int) -> Optional[FamilyDTO]:
    """
    Updates a single entry with the new values passed.

    :param str import_id: The family import id to change.
    :param FamilyDTO family: The new values
    :param int geo_id: a validated geography id
    :return Optional[FamilyDTO]: The new values set or None if not found.
    """
    new_values = family.dict()
    # TODO : Update more values on a family
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
        return

    return get(db, family.import_id)


def create(db: Session, family: FamilyDTO, geo_id: int) -> Optional[FamilyDTO]:
    """
    Creates a new family.

    :param FamilyDTO family: the values for the new family
    :param int geo_id: a validated geography id
    :return Optional[FamilyDTO]: the new family created
    """
    try:
        new_family = _family_from_dto(family, geo_id)
        db.add(new_family)
    except Exception as e:
        _LOGGER.error(e)
        return

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
