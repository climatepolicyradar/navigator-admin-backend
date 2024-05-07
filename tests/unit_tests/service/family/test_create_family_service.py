"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import AuthorisationError, ValidationError
from tests.helpers.family import create_family_create_dto

USER_EMAIL = "test@cpr.org"
ORG_ID = 1


# --- CREATE


def test_create(
    family_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
):
    new_family = create_family_create_dto(collections=["x.y.z.1", "x.y.z.2"])
    family = family_service.create(new_family, USER_EMAIL)
    assert family is not None

    assert family_repo_mock.create.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert corpus_repo_mock.validate.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1


def test_create_repo_fails(
    family_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    app_user_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
):
    new_family = create_family_create_dto(collections=["x.y.z.1", "x.y.z.2"])
    family_repo_mock.return_empty = True
    family = family_service.create(new_family, USER_EMAIL)

    # TODO: Should this be a RepositoryError
    assert family == ""

    assert family_repo_mock.create.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert corpus_repo_mock.validate.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1


def test_create_raises_when_category_invalid(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
):
    new_family = create_family_create_dto(collections=["x.y.z.1", "x.y.z.2"])
    new_family.category = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, USER_EMAIL)
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0
    assert corpus_repo_mock.validate.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0


def test_create_raises_when_metadata_invalid(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
):
    new_family = create_family_create_dto(collections=["x.y.z.1", "x.y.z.2"])
    metadata_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, USER_EMAIL)
    expected_msg = "Organisation 1 has no Taxonomy defined!"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0
    assert corpus_repo_mock.validate.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0


def test_create_raises_when_collection_org_different_to_usr_org(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
):
    new_family = create_family_create_dto(collections=["x.y.z.1", "x.y.z.2"])
    collection_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        family_service.create(new_family, USER_EMAIL)
    expected_msg = "Organisation mismatch between some collections and the current user"

    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert corpus_repo_mock.validate.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0


def test_create_raises_when_corpus_missing(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
):
    new_family = create_family_create_dto(collections=["x.y.z.1", "x.y.z.2"])
    corpus_repo_mock.valid = False
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, USER_EMAIL)
    expected_msg = "Corpus 'CCLW.corpus.i00000001.n0000' not found"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert corpus_repo_mock.validate.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0


def test_create_raises_when_corpus_org_different_to_usr_org(
    family_repo_mock,
    geography_repo_mock,
    app_user_repo_mock,
    metadata_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
):
    new_family = create_family_create_dto(collections=["x.y.z.1", "x.y.z.2"])
    corpus_repo_mock.error = True
    with pytest.raises(AuthorisationError) as e:
        family_service.create(new_family, USER_EMAIL)
    expected_msg = "Organisation mismatch between selected corpus and the current user"

    assert e.value.message == expected_msg

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.create.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert metadata_repo_mock.get_schema_for_org.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert corpus_repo_mock.validate.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
