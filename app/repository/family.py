"""Operations on the repository for the Family entity."""

from datetime import datetime
from typing import Optional
from app.db.models.law_policy.collection import CollectionFamily
from sqlalchemy.orm import Session
from app.model.family import FamilyDTO
from app.db.models.law_policy import Family


THE_REPO: list[FamilyDTO] = [
    FamilyDTO(
        import_id="sample1",
        title="title",
        summary="summary",
        geography="geo",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=datetime.now(),
        last_updated_date=datetime.now(),
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    ),
    FamilyDTO(
        import_id="sample2",
        title="title two",
        summary="summary",
        geography="geo",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=datetime.now(),
        last_updated_date=datetime.now(),
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    ),
]


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


def get(import_id: str) -> Optional[FamilyDTO]:
    """
    Gets a single family from the repository.

    :param str import_id: The import_id of the family
    :return Optional[FamilyResponse]: A single family or nothing
    """
    found = [r for r in THE_REPO if r.import_id == import_id]

    if len(found) == 0:
        return

    return found[0]


def search(search_term: str) -> Optional[list[FamilyDTO]]:
    """
    Gets a list of families from the repository searching title and summary.

    :param str search_term: Any search term to filter on title or summary
    :return Optional[list[FamilyResponse]]: A list of matches
    """
    found = [r for r in THE_REPO if search_term in r.title or search_term in r.summary]

    return found


def update(import_id: str, family: FamilyDTO) -> Optional[FamilyDTO]:
    """
    Updates a single entry with the new values passed.

    :param str import_id: The family import id to change.
    :param FamilyDTO family: The new values
    :return Optional[FamilyDTO]: The new values set or None if not found.
    """
    found = [i for i, r in enumerate(THE_REPO) if r.import_id == import_id]
    if len(found) == 0:
        return None

    # Now update the entry
    index = found[0]
    THE_REPO[index] = family

    return family


def create(family: FamilyDTO) -> Optional[FamilyDTO]:
    """
    Creates a new family.

    :param FamilyDTO family: the values for the new family
    :return Optional[FamilyDTO]: the new family created
    """
    found = [r for r in THE_REPO if r.import_id == family.import_id]
    if len(found) > 0:
        return

    THE_REPO.append(family)
    return family


def delete(import_id: str) -> bool:
    """
    Deletes a single family by the import id.

    :param str import_id: The family import id to delete.
    :return bool: True if deleted False if not.
    """
    found = [i for i, r in enumerate(THE_REPO) if r.import_id == import_id]
    if len(found) == 0:
        return False

    # Now update the entry
    index = found[0]
    del THE_REPO[index]

    return True
