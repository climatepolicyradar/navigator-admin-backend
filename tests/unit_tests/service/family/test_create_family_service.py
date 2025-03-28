"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import AuthorisationError, RepositoryError, ValidationError
from tests.helpers.family import create_family_create_dto


def test_create(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    family = family_service.create(new_family, admin_user_context)
    assert family is not None

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert family_repo_mock.create.call_count == 1


def test_create_repo_fails(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    family_repo_mock.throw_repository_error = True

    with pytest.raises(RepositoryError) as e:
        family_service.create(new_family, admin_user_context)

    expected_msg = "bad family repo"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 1
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert family_repo_mock.create.call_count == 1


def test_create_raises_when_category_invalid(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    new_family.category = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, admin_user_context)
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 0
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0
    assert family_repo_mock.create.call_count == 0


def test_create_raises_when_missing_metadata(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    collections = ["x.y.z.1", "x.y.z.2"]
    new_family = create_family_create_dto(
        collections=collections, metadata={"color": ["blue"]}
    )
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, admin_user_context)
    expected_msg = "Metadata validation failed: Missing metadata keys: {'size'}"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 1
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == len(
        collections
    )
    assert family_repo_mock.create.call_count == 0


def test_create_raises_when_missing_taxonomy(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    collections = ["x.y.z.1", "x.y.z.2"]
    db_client_metadata_mock.bad_taxonomy = True
    new_family = create_family_create_dto(
        collections=collections, metadata={"size": ["100"], "color": ["blue"]}
    )
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, admin_user_context)
    expected_msg = "No taxonomy found for corpus"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 1
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == len(
        collections
    )
    assert family_repo_mock.create.call_count == 0


def test_create_raises_when_collection_org_different_to_usr_org(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    collection_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        family_service.create(new_family, admin_user_context)
    expected_msg = "Organisation mismatch between some collections and the current user"

    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 0
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert family_repo_mock.create.call_count == 0


def test_create_raises_when_corpus_missing(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    corpus_repo_mock.valid = False
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, admin_user_context)
    expected_msg = "Corpus 'CCLW.corpus.i00000001.n0000' not found"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 0
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0
    assert family_repo_mock.create.call_count == 0


def test_create_when_no_org_associated_with_entity(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    admin_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    corpus_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, admin_user_context)

    expected_msg = "No organisation associated with corpus CCLW.corpus.i00000001.n0000"
    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 0
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0
    assert family_repo_mock.create.call_count == 0


def test_create_raises_when_corpus_org_different_to_usr_org(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    another_admin_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    with pytest.raises(AuthorisationError) as e:
        family_service.create(new_family, another_admin_user_context)
    expected_msg = "User 'another-admin@here.com' is not authorised to perform operation on 'CCLW.corpus.i00000001.n0000'"

    assert e.value.message == expected_msg

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 0
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert family_repo_mock.create.call_count == 0


def test_create_success_when_corpus_org_different_to_usr_org_super(
    family_repo_mock,
    geography_repo_mock,
    collection_repo_mock,
    corpus_repo_mock,
    db_client_metadata_mock,
    super_user_context,
):
    new_family = create_family_create_dto(
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    family = family_service.create(new_family, super_user_context)
    assert family is not None

    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert corpus_repo_mock.verify_corpus_exists.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert db_client_metadata_mock.get_taxonomy_from_corpus.call_count == 1
    assert db_client_metadata_mock.get_entity_specific_taxonomy.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 2
    assert family_repo_mock.create.call_count == 1


def test_create_endpoint_raises_validation_error_when_validating_invalid_geographies(
    family_repo_mock,
    geography_repo_mock,
    admin_user_context,
):
    new_family = create_family_create_dto(
        geographies=["123"],
        collections=["x.y.z.1", "x.y.z.2"],
        metadata={"size": ["100"], "color": ["blue"]},
    )
    geography_repo_mock.error = True

    with pytest.raises(ValidationError) as e:
        family_service.create(new_family, admin_user_context)

    expected_msg = "One or more of the following geography values are invalid: 123"
    assert e.value.message == expected_msg
    assert geography_repo_mock.get_ids_from_values.call_count == 1
    assert family_repo_mock.create.call_count == 0
