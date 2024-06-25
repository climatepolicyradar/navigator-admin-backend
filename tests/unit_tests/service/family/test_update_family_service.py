"""
Tests the family service.

Uses a family repo mock and ensures that the repo is called.
"""

import pytest

import app.service.family as family_service
from app.errors import AuthorisationError, ValidationError
from tests.helpers.family import create_family_write_dto


def test_update(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None
    family_repo_mock.get.call_count = 0
    assert family_repo_mock.get.call_count == 0

    updated_family = create_family_write_dto(
        title="UPDATED TITLE",
        collections=["x.y.z.2", "x.y.z.3"],
        metadata={"size": [100], "color": ["blue"]},
    )
    result = family_service.update("a.b.c.d", admin_user_context, updated_family)
    assert result is not None

    assert family_repo_mock.update.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3
    assert family_repo_mock.get.call_count == 2


def test_update_when_family_missing(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None
    family_repo_mock.get.call_count = 0
    assert family_repo_mock.get.call_count == 0

    updated_family = create_family_write_dto(
        metadata={"size": [100], "color": ["blue"]}
    )
    family_repo_mock.return_empty = True
    result = family_service.update("a.b.c.d", admin_user_context, updated_family)
    assert result is None

    assert family_repo_mock.update.call_count == 0
    assert geography_repo_mock.get_id_from_value.call_count == 0
    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_family_id_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family_repo_mock.get.call_count = 0
    assert family_repo_mock.get.call_count == 0

    updated_family = create_family_write_dto(
        metadata={"size": [100], "color": ["blue"]}
    )
    family.import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        family_service.update(family.import_id, admin_user_context, updated_family)
    expected_msg = f"The import id {family.import_id} is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 0
    assert geography_repo_mock.get_id_from_value.call_count == 0
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_category_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family_repo_mock.get.call_count = 0
    assert family_repo_mock.get.call_count == 0

    updated_family = create_family_write_dto(
        category="invalid", metadata={"size": [100], "color": ["blue"]}
    )

    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "Invalid is not a valid FamilyCategory"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 0
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_raises_when_organisation_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family_repo_mock.get.call_count = 0
    assert family_repo_mock.get.call_count == 0

    updated_family = create_family_write_dto(
        metadata={"size": [100], "color": ["blue"]}
    )

    corpus_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)

    expected_msg = "No organisation associated with corpus CCLW.corpus.i00000001.n0000"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_geography_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright
    family_repo_mock.get.call_count = 0
    assert family_repo_mock.get.call_count == 0

    updated_family = create_family_write_dto(
        metadata={"size": [100], "color": ["blue"]}
    )

    geography_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "The geography value CHN is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_metadata_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(metadata={"invalid": True})

    metadata_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)

    expected_message = "Metadata validation failed: "
    expected_missing_message = "[\"Missing metadata keys: {'size', 'color'}\""
    expected_extra_message = "\"Extra metadata keys: {'invalid'}\"]"

    assert e.value.message.startswith(expected_message)
    assert len(e.value.message) == len(
        expected_message + expected_missing_message + ", " + expected_extra_message
    )
    assert (
        e.value.message
        == expected_message + expected_missing_message + ", " + expected_extra_message
    )

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_id_invalid(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(
        collections=["x.y.z.2", "col3", "col4"],
        metadata={"size": [100], "color": ["blue"]},
    )

    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "The import ids are invalid: ['col3', 'col4']"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert collection_repo_mock.validate.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_missing(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(
        metadata={"size": [100], "color": ["blue"]}
    )

    collection_repo_mock.missing = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "One or more of the collections to update does not exist"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert collection_repo_mock.validate.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0


def test_update_family_raises_when_collection_org_different_to_usr_org(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(
        collections=["x.y.z.2", "x.y.z.3"], metadata={"size": [100], "color": ["blue"]}
    )

    collection_repo_mock.alternative_org = True
    with pytest.raises(ValidationError) as e:
        family_service.update("a.b.c.d", admin_user_context, updated_family)
    expected_msg = "Organisation mismatch between some collections and the current user"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3
    assert collection_repo_mock.validate.call_count == 1


def test_update_raises_when_family_organisation_mismatch_with_user_org(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    another_admin_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family is not None  # needed to placate pyright

    updated_family = create_family_write_dto(
        collections=["x.y.z.2", "x.y.z.3"], metadata={"size": [100], "color": ["blue"]}
    )

    with pytest.raises(AuthorisationError) as e:
        ok = family_service.update(
            "a.b.c.d", another_admin_user_context, updated_family
        )
        assert not ok

    expected_msg = "User 'another-admin@here.com' is not authorised to perform operation on 'CCLW.corpus.i00000001.n0000'"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 2
    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.update.call_count == 0
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert collection_repo_mock.get_org_from_collection_id.call_count == 0
    assert collection_repo_mock.validate.call_count == 0


def test_update_success_when_family_organisation_mismatch_with_user_org(
    family_repo_mock,
    collection_repo_mock,
    geography_repo_mock,
    metadata_repo_mock,
    corpus_repo_mock,
    super_user_context,
):
    family = family_service.get("a.b.c.d")
    assert family_repo_mock.get.call_count == 1
    assert family is not None
    family_repo_mock.get.call_count = 0

    updated_family = create_family_write_dto(
        title="UPDATED TITLE",
        collections=["x.y.z.2", "x.y.z.3"],
        metadata={"size": [100], "color": ["blue"]},
    )
    result = family_service.update("a.b.c.d", super_user_context, updated_family)
    assert result is not None

    assert geography_repo_mock.get_id_from_value.call_count == 1
    assert family_repo_mock.get.call_count == 2
    assert corpus_repo_mock.get_corpus_org_id.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert collection_repo_mock.get_org_from_collection_id.call_count == 3
    assert collection_repo_mock.validate.call_count == 1
    assert family_repo_mock.update.call_count == 1
