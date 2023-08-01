"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""
import pytest
from app.errors.validation_error import ValidationError
from app.model.family import FamilyDTO
import app.service.family as family_service
from unit_tests.mocks.family_repo import FAIL_ID, MISSING_ID, VALID_ID

# --- GET


def test_get_family_returns_family_if_exists(family_repo_mock):
    result = family_service.get(VALID_ID)
    assert result is not None
    assert family_repo_mock.get.call_count == 1


def test_get_family_returns_none_if_missing(family_repo_mock):
    result = family_service.get(MISSING_ID)
    assert result is None
    assert family_repo_mock.get.call_count == 1


def test_get_family_raises_if_invalid_id(family_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.get(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.get.call_count == 0


# --- SEARCH


def test_search_families(family_repo_mock):
    result = family_service.search("two")
    assert result is not None
    assert len(result) == 1
    assert family_repo_mock.search.call_count == 1


def test_search_families_missing(family_repo_mock):
    result = family_service.search("empty")
    assert result is not None
    assert len(result) == 0
    assert family_repo_mock.search.call_count == 1


# --- DELETE


def test_delete_family(family_repo_mock):
    ok = family_service.delete(VALID_ID)
    assert ok
    assert family_repo_mock.delete.call_count == 1


def test_delete_family_missing(family_repo_mock):
    ok = family_service.delete(MISSING_ID)
    assert not ok
    assert family_repo_mock.delete.call_count == 1


def test_delete_family_raises_if_invalid_id(family_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.delete(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.delete.call_count == 0


# --- UPDATE


def test_update_family(family_repo_mock, geography_service_mock):
    family = family_service.get(VALID_ID)
    assert family is not None
    family.slug = "snail"

    result = family_service.update(family)
    assert result is not None
    assert result.slug == "snail"
    assert family_repo_mock.update.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_service_mock.validate.call_count == 1


def test_update_family_missing(family_repo_mock, geography_service_mock):
    family = family_service.get(VALID_ID)
    assert family is not None
    family.import_id = MISSING_ID

    result = family_service.update(family)
    assert result is None
    assert family_repo_mock.update.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_service_mock.validate.call_count == 1


def test_update_family_raises_if_invalid_id(family_repo_mock):
    family = family_service.get(VALID_ID)
    assert family is not None
    family.import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.update(family)
    expected_msg = f"The import id {family.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.update.call_count == 0


# --- CREATE


def test_create_family(family_repo_mock, geography_service_mock):
    new_family = FamilyDTO(
        import_id="A.0.0.5",
        title="This is a test",
        summary="summary",
        geography="GBR",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )
    family = family_service.create(new_family)
    assert family is not None
    assert family_repo_mock.create.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_service_mock.validate.call_count == 1


def test_create_family_error(family_repo_mock, geography_service_mock):
    new_family = FamilyDTO(
        import_id=FAIL_ID,
        title="This is a test",
        summary="summary",
        geography="GBR",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )
    family = family_service.create(new_family)
    assert family is None
    assert family_repo_mock.create.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_service_mock.validate.call_count == 1


def test_create_family_raises_if_invalid_id(family_repo_mock):
    new_family = FamilyDTO(
        import_id="invalid",
        title="invalid",
        summary="summary",
        geography="GBR",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family)
    expected_msg = f"The import id {new_family.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.create.call_count == 0
