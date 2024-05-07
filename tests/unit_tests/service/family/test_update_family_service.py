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
