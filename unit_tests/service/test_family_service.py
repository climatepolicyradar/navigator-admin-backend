"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""
from typing import Optional

import pytest

import app.service.family as family_service
from app.errors import RepositoryError, ValidationError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from unit_tests.helpers.family import create_family_dto

USER_EMAIL = "test@cpr.org"
ORG_ID = 1


def to_write_dto(
    dto: FamilyReadDTO, collections: Optional[list[str]] = ["x.y.z.2", "x.y.z.3"]
) -> FamilyWriteDTO:
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
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family_repo_mock.get.call_count == 1
    assert family is not None
    family_repo_mock.get.call_count = 0

    result = family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))
    assert result is not None

    assert family_repo_mock.update.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3
    assert family_repo_mock.get.call_count == 2


def test_update_when_family_missing(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None

    family_repo_mock.return_empty = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))
    assert e.value.message == "Could not find family a.b.c.d"

    assert family_repo_mock.update.call_count == 0
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.get.call_count == 2
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_family_id_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    family.import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.update(family.import_id, USER_EMAIL, to_write_dto(family))
    expected_msg = f"The import id {family.import_id} is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 0
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_category_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family.category = "invalid"

    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 0
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_organisation_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    organisation_repo_mock.error = True
    app_user_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))

    expected_msg = "The organisation name CCLW is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_geography_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    geography_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))
    expected_msg = "The geography value CHN is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_metadata_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    family.metadata = {"invalid": True}
    metadata_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))
    expected_msg = "Organisation 1 has no Taxonomy defined!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_id_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    with pytest.raises(ValidationError) as e:
        family_service.update(
            "a.b.c.d", USER_EMAIL, to_write_dto(family, ["x.y.z.2", "col3", "col4"])
        )
    expected_msg = "The import ids are invalid: ['col3', 'col4']"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_org_different_to_usr_org(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    collection_repo_mock.invalid_org = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))
    expected_msg = "Organisation mismatch between some collections and the current user"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3


def test_update_family_raises_when_collection_missing(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    collection_repo_mock.missing = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", USER_EMAIL, to_write_dto(family))
    expected_msg = "Organisation mismatch between some collections and the current user"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3


# --- CREATE


def test_create(
    family_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
    collection_repo_mock,
):
    new_family = create_family_dto(import_id="A.0.0.5")
    family = family_service.create(to_create_dto(new_family), USER_EMAIL)
    assert family is not None

    assert family_repo_mock.create.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2


def test_create_repo_fails(
    family_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
    collection_repo_mock,
):
    new_family = create_family_dto(import_id="a.b.c.d")
    family_repo_mock.return_empty = True
    family = family_service.create(to_create_dto(new_family), USER_EMAIL)

    # TODO: Should this be a RepositoryError
    assert family == ""

    assert family_repo_mock.create.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2


def test_create_raises_when_category_invalid(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
):
    new_family = create_family_dto(import_id="A.0.0.5")
    new_family.category = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.create(to_create_dto(new_family), USER_EMAIL)
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_create_raises_when_metadata_invalid(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
):
    new_family = create_family_dto(import_id="A.0.0.5")
    metadata_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.create(to_create_dto(new_family), USER_EMAIL)
    expected_msg = "Organisation 1 has no Taxonomy defined!"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_create_raises_when_collection_org_different_to_usr_org(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
):
    new_family = create_family_dto(import_id="A.0.0.5")
    collection_repo_mock.alternative_org = True
    with pytest.raises(ValidationError) as e:
        family_service.create(to_create_dto(new_family), USER_EMAIL)
    expected_msg = "Organisation mismatch between some collections and the current user"

    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2


def test_create_raises_when_collection_missing(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
):
    new_family = create_family_dto(import_id="A.0.0.5")
    collection_repo_mock.missing = True
    with pytest.raises(ValidationError) as e:
        family_service.create(to_create_dto(new_family), USER_EMAIL)
    expected_msg = "Organisation mismatch between some collections and the current user"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2


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
