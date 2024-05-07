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


# --- SEARCH


def test_search(family_repo_mock):
    result = family_service.search({"q": "two"})
    assert result is not None
    assert len(result) == 2
    assert family_repo_mock.search.call_count == 1


def test_search_on_specific_field(family_repo_mock):
    result = family_service.search({"title": "one"})
    assert result is not None
    assert len(result) == 1
    assert family_repo_mock.search.call_count == 1


def test_search_db_error(family_repo_mock):
    family_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        family_service.search({"q": "error"})
    assert family_repo_mock.search.call_count == 1


def test_search_request_timeout(family_repo_mock):
    family_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        family_service.search({"q": "timeout"})
    assert family_repo_mock.search.call_count == 1


def test_search_missing(family_repo_mock):
    family_repo_mock.return_empty = True
    result = family_service.search({"q": "empty"})
    assert result is not None
    assert len(result) == 0
    assert family_repo_mock.search.call_count == 1
