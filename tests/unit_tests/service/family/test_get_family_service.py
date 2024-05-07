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


# --- GET


def test_get_returns_family_if_exists(family_repo_mock):
    result = family_service.get("a.b.c.d")
    assert result is not None
    assert family_repo_mock.get.call_count == 1


def test_get_returns_none_if_missing(family_repo_mock):
    family_repo_mock.return_empty = True
    result = family_service.get("a.b.c.d")
    assert result is None
    assert family_repo_mock.get.call_count == 1


def test_get_raises_when_invalid_id(family_repo_mock):
    with pytest.raises(ValidationError) as e:
        family_service.get("a.b.c")
    expected_msg = "The import id a.b.c is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.get.call_count == 0
