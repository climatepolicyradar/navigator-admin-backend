"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

from typing import Optional

import pytest

import app.service.family as family_service
from app.errors import RepositoryError
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


# --- COUNT


def test_count(family_repo_mock):
    result = family_service.count()
    assert result is not None
    assert family_repo_mock.count.call_count == 1


def test_count_returns_none(family_repo_mock):
    family_repo_mock.return_empty = True
    result = family_service.count()
    assert result is None
    assert family_repo_mock.count.call_count == 1


def test_count_raises_if_db_error(family_repo_mock):
    family_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        family_service.count()

    expected_msg = "bad repo"
    assert e.value.message == expected_msg
    assert family_repo_mock.count.call_count == 1
