"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

from typing import Optional

import pytest

import app.service.family as family_service
from app.errors import ValidationError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO

USER_EMAIL = "test@cpr.org"
ORG_ID = 1


def to_write_dto(
    dto: FamilyReadDTO, collections: Optional[list[str]] = None
) -> FamilyWriteDTO:
    if collections is None:
        collections = ["x.y.z.2", "x.y.z.3"]
    if collections is None:
        collections = dto.collections
    return FamilyWriteDTO(
        title=dto.title,
        summary=dto.summary,
        geography=dto.geography,
        category=dto.category,
        metadata=dto.metadata,
        collections=collections,
    )


def to_create_dto(dto: FamilyReadDTO) -> FamilyCreateDTO:
    return FamilyCreateDTO(
        title=dto.title,
        summary=dto.summary,
        geography=dto.geography,
        category=dto.category,
        metadata=dto.metadata,
        collections=dto.collections,
        corpus_import_id=dto.corpus_import_id,
    )


# --- DELETE


def test_delete(family_repo_mock):
    ok = family_service.delete("a.b.c.d")
    assert ok
    assert family_repo_mock.delete.call_count == 1


def test_delete_when_family_missing(family_repo_mock):
    family_repo_mock.return_empty = True
    ok = family_service.delete("a.b.c.d")
    assert not ok
    assert family_repo_mock.delete.call_count == 0


def test_delete_raises_when_invalid_id(family_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.delete(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.delete.call_count == 0
