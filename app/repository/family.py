"""Operations on the repository for the Family entity."""

from datetime import datetime
from typing import Optional
from app.model.family import FamilyDTO

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


def get_all_families() -> list[FamilyDTO]:
    """
    Returns all the families.

    :return Optional[FamilyResponse]: All of things
    """
    return THE_REPO


def get_family(import_id: str) -> Optional[FamilyDTO]:
    """
    Gets a single family from the repository.

    :param str import_id: The import_id of the family
    :return Optional[FamilyResponse]: A single family or nothing
    """
    found = [r for r in THE_REPO if r.import_id == import_id]

    if len(found) == 0:
        return

    return found[0]


def search_families(search_term: str) -> Optional[list[FamilyDTO]]:
    """
    Gets a list of families from the repository searching title and summary.

    :param str search_term: Any search term to filter on title or summary
    :return Optional[list[FamilyResponse]]: A list of matches
    """
    found = [r for r in THE_REPO if search_term in r.title or search_term in r.summary]

    return found


def update_family(import_id: str, family: FamilyDTO) -> Optional[FamilyDTO]:
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


def create_family(family: FamilyDTO) -> Optional[FamilyDTO]:
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


def delete_family(import_id: str) -> bool:
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
