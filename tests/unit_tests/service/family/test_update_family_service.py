"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import ValidationError
from tests.helpers.family import create_family_write_dto

# --- UPDATE


def test_update(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family_repo_mock.get.call_count == 1
    assert family is not None
    family_repo_mock.get.call_count = 0

    updated_family = create_family_write_dto(
        title="UPDATED TITLE", collections=["x.y.z.2", "x.y.z.3"]
    )
    result = family_service.update("a.b.c.d", admin_user_context, updated_family)
    assert result is not None

    assert family_repo_mock.update.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3
    assert family_repo_mock.get.call_count == 2


def test_update_when_family_missing(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None

    updated_family = create_family_write_dto()
    family_repo_mock.return_empty = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    assert e.value.message == "Could not find family a.b.c.d"

    assert family_repo_mock.update.call_count == 0
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.get.call_count == 2
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_family_id_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto()
    family.import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.update(family.import_id, admin_user_context, updated_family)
    expected_msg = f"The import id {family.import_id} is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 0
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_category_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(category="invalid")

    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 0
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_organisation_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto()

    organisation_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)

    expected_msg = "The organisation name CCLW is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_geography_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto()

    geography_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "The geography value CHN is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 0
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_metadata_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(metadata={"invalid": True})

    metadata_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "Organisation 1 has no Taxonomy defined!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_id_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(collections=["x.y.z.2", "col3", "col4"])

    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "The import ids are invalid: ['col3', 'col4']"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.validate.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_missing(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto()

    collection_repo_mock.missing = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "One or more of the collections to update does not exist"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.validate.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_org_different_to_usr_org(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    organisation_repo_mock,
    metadata_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(collections=["x.y.z.2", "x.y.z.3"])

    collection_repo_mock.invalid_org = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "Organisation mismatch between some collections and the current user"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert organisation_repo_mock.get_id_from_name.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3
    assert collection_repo_mock.validate.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3
