"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""
import pytest
from app.errors import ValidationError
from app.model.family import FamilyReadDTO, FamilyWriteDTO
import app.service.family as family_service
from unit_tests.helpers.family import create_family_dto


def to_write_dto(dto: FamilyReadDTO) -> FamilyWriteDTO:
    return FamilyWriteDTO(
        import_id=dto.import_id,
        title=dto.title,
        summary=dto.summary,
        geography=dto.geography,
        category=dto.category,
        metadata=dto.metadata,
        organisation=dto.organisation,
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


# --- SEARCH


def test_search(family_repo_mock):
    result = family_service.search("two")
    assert result is not None
    assert len(result) == 1
    assert family_repo_mock.search.call_count == 1


def test_search_missing(family_repo_mock):
    family_repo_mock.return_empty = True
    result = family_service.search("empty")
    assert result is not None
    assert len(result) == 0
    assert family_repo_mock.search.call_count == 1


# --- DELETE


def test_delete(family_repo_mock):
    ok = family_service.delete("a.b.c.d")
    assert ok
    assert family_repo_mock.delete.call_count == 1


def test_delete_missing(family_repo_mock):
    family_repo_mock.return_empty = True
    ok = family_service.delete("a.b.c.d")
    assert not ok
    assert family_repo_mock.delete.call_count == 1


def test_delete_raises_when_invalid_id(family_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.delete(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.delete.call_count == 0


# --- UPDATE


def test_update(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None

    result = family_service.update(to_write_dto(family))
    assert result is not None
    assert family_repo_mock.update.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1


def test_update_when_missing(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None
    family_repo_mock.return_empty = True

    result = family_service.update(to_write_dto(family))
    assert result is None
    assert family_repo_mock.update.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_repo_mock.get_id_from_value.call_count == 1


def test_update_raises_when_id_invalid(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family.import_id = "invalid"

    with pytest.raises(ValidationError) as e:
        family_service.update(to_write_dto(family))
    expected_msg = f"The import id {family.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.update.call_count == 0


def test_update_raises_when_category_invalid(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family.category = "invalid"

    with pytest.raises(ValidationError) as e:
        family_service.update(to_write_dto(family))
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg
    assert family_repo_mock.update.call_count == 0


def test_update_raises_when_organisation_invalid(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    organisation_repo_mock.error = True

    with pytest.raises(ValidationError) as e:
        family_service.update(to_write_dto(family))

    expected_msg = "The organisation name test_org is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.update.call_count == 0


def test_update_family_raises_when_geography_invalid(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    geography_repo_mock.error = True

    with pytest.raises(ValidationError) as e:
        family_service.update(to_write_dto(family))
    expected_msg = "The geography value CHN is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.update.call_count == 0


def test_update_family_raises_when_metadata_invalid(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family.metadata = {"invalid": True}
    metadata_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update(to_write_dto(family))
    expected_msg = "Organisation 1 has no Taxonomy defined!"
    assert e.value.message == expected_msg
    assert family_repo_mock.update.call_count == 0


# --- CREATE


def test_create(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    new_family = create_family_dto(import_id="A.0.0.5")
    family = family_service.create(to_write_dto(new_family))
    assert family is not None
    assert family_repo_mock.create.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1


def test_create_repo_fails(
    family_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
):
    new_family = create_family_dto(import_id="a.b.c.d")
    family_repo_mock.return_empty = True
    family = family_service.create(to_write_dto(new_family))
    assert family is None
    assert family_repo_mock.create.call_count == 1
    # Ensure the family service uses the geo service to validate
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1


def test_create_raises_when_id_invalid(family_repo_mock):
    new_family = create_family_dto(import_id="invalid")
    with pytest.raises(ValidationError) as e:
        family_service.create(to_write_dto(new_family))
    expected_msg = f"The import id {new_family.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert family_repo_mock.create.call_count == 0


def test_create_raises_when_category_invalid(family_repo_mock, geography_repo_mock):
    new_family = create_family_dto(import_id="A.0.0.5")
    new_family.category = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.create(to_write_dto(new_family))
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg
    assert family_repo_mock.create.call_count == 0
