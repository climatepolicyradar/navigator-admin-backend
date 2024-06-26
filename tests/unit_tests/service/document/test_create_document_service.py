import pytest

import app.service.document as doc_service
from app.errors import AuthorisationError, RepositoryError, ValidationError
from tests.helpers.document import create_document_create_dto


def test_create(document_repo_mock, family_repo_mock, admin_user_context):
    new_document = create_document_create_dto()
    document = doc_service.create(new_document, admin_user_context)
    assert document is not None

    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert document_repo_mock.create.call_count == 1


def test_create_when_db_fails(document_repo_mock, family_repo_mock, admin_user_context):
    new_document = create_document_create_dto()
    document_repo_mock.return_empty = True

    with pytest.raises(RepositoryError):
        doc_service.create(new_document, admin_user_context)

    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert document_repo_mock.create.call_count == 1


def test_create_raises_when_invalid_family_id(
    document_repo_mock, family_repo_mock, admin_user_context
):
    new_document = create_document_create_dto(family_import_id="invalid family")
    with pytest.raises(ValidationError) as e:
        doc_service.create(new_document, admin_user_context)

    expected_msg = f"The import id {new_document.family_import_id} is invalid!"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 0
    assert family_repo_mock.get_organisation.call_count == 0
    assert document_repo_mock.create.call_count == 0


def test_create_raises_when_blank_variant(
    document_repo_mock, family_repo_mock, admin_user_context
):
    new_document = create_document_create_dto(variant_name="")
    with pytest.raises(ValidationError) as e:
        doc_service.create(new_document, admin_user_context)
    expected_msg = "Variant name is empty"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 0
    assert family_repo_mock.get_organisation.call_count == 0
    assert document_repo_mock.create.call_count == 0


def test_create_when_no_org_associated_with_entity(
    document_repo_mock, family_repo_mock, admin_user_context
):
    new_document = create_document_create_dto()
    family_repo_mock.no_org = True
    with pytest.raises(ValidationError) as e:
        ok = doc_service.create(new_document, admin_user_context)
        assert not ok

    expected_msg = "No organisation associated with import id test.family.1.0"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert document_repo_mock.create.call_count == 0


def test_create_raises_when_org_mismatch(
    document_repo_mock, family_repo_mock, another_admin_user_context
):
    new_document = create_document_create_dto()
    family_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        ok = doc_service.create(new_document, another_admin_user_context)
        assert not ok

    expected_msg = "User 'another-admin@here.com' is not authorised to perform operation on 'test.family.1.0'"
    assert e.value.message == expected_msg

    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert document_repo_mock.create.call_count == 0


def test_create_success_when_org_mismatch(
    document_repo_mock, family_repo_mock, super_user_context
):
    new_document = create_document_create_dto()
    document = doc_service.create(new_document, super_user_context)
    assert document is not None

    assert family_repo_mock.get.call_count == 1
    assert family_repo_mock.get_organisation.call_count == 1
    assert document_repo_mock.create.call_count == 1
