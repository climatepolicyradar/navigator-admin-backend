"""Operations on the repository for the Family entity."""

import logging
from typing import Optional
from app.db.models.law_policy.collection import CollectionFamily
from sqlalchemy.orm import Session
from app.model.family import FamilyDTO
from app.db.models.law_policy import Family
from sqlalchemy.exc import NoResultFound
from sqlalchemy_utils import escape_like
from sqlalchemy import or_, update as db_update, delete as db_delete


_LOGGER = logging.getLogger(__name__)


def _family_from_dto(dto: FamilyDTO) -> Family:
    return Family(
        import_id=dto.import_id,
        title=dto.title,
        description=dto.summary,
        geography_id=int(dto.geography),
        family_category=dto.category,
    )


def _family_to_dto(db: Session, f: Family) -> FamilyDTO:
    return FamilyDTO(
        import_id=str(f.import_id),
        title=str(f.title),
        summary=str(f.description),
        geography=str(f.geography_id),
        category=str(f.family_category),
        status=str(f.family_status),
        metadata={},  # TODO: organisation and metadata
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
    families = db.query(Family).all()

    if not families:
        return []

    result = [_family_to_dto(db, f) for f in families]

    return result


def get(db: Session, import_id: str) -> Optional[FamilyDTO]:
    """
    Gets a single family from the repository.

    :param str import_id: The import_id of the family
    :return Optional[FamilyResponse]: A single family or nothing
    """
    try:
        family = db.query(Family).filter(Family.import_id == import_id).one()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _family_to_dto(db, family)


def search(db: Session, search_term: str) -> list[FamilyDTO]:
    """
    Gets a list of families from the repository searching title and summary.

    :param str search_term: Any search term to filter on title or summary
    :return Optional[list[FamilyResponse]]: A list of matches
    """
    term = f"%{escape_like(search_term)}%"
    search = or_(Family.title.ilike(term), Family.description.ilike(term))
    found = db.query(Family).filter(search).all()

    return [_family_to_dto(db, f) for f in found]


def update(db: Session, family: FamilyDTO) -> Optional[FamilyDTO]:
    """
    Updates a single entry with the new values passed.

    :param str import_id: The family import id to change.
    :param FamilyDTO family: The new values
    :return Optional[FamilyDTO]: The new values set or None if not found.
    """
    new_values = family.dict()
    # TODO : Update more values on a family
    result = db.execute(
        db_update(Family)
        .where(Family.import_id == family.import_id)
        .values(title=new_values["title"], description=new_values["summary"])
    )

    if result.rowcount == 0:  # type: ignore
        return

    return get(db, family.import_id)


def create(db: Session, family: FamilyDTO) -> Optional[FamilyDTO]:
    """
    Creates a new family.

    :param FamilyDTO family: the values for the new family
    :return Optional[FamilyDTO]: the new family created
    """
    try:
        new_family = _family_from_dto(family)
        db.add(new_family)
        db.commit()
    except Exception as e:
        _LOGGER.error(e)
        return

    return get(db, str(new_family.import_id))


def delete(db: Session, import_id: str) -> bool:
    """
    Deletes a single family by the import id.

    :param str import_id: The family import id to delete.
    :return bool: True if deleted False if not.
    """
    result = db.execute(db_delete(Family).where(Family.import_id == import_id))
    db.commit()

    return result.rowcount > 0  # type: ignore
