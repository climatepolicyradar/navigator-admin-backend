import pytest

import app.service.document as doc_service
from app.errors import AuthorisationError, RepositoryError, ValidationError
from tests.helpers.document import create_document_write_dto

USER_EMAIL = "test@cpr.org"


def test_update(document_repo_mock, app_user_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto()
    result = doc_service.update(document.import_id, updated_doc, USER_EMAIL)
    assert result is not None

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.update.call_count == 1
    assert document_repo_mock.get.call_count == 1


def test_update_when_missing(document_repo_mock, app_user_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    document_repo_mock.return_empty = True
    updated_doc = create_document_write_dto()
    with pytest.raises(RepositoryError) as e:
        doc_service.update(document.import_id, updated_doc, USER_EMAIL)
    assert e.value.message == "Error when updating document a.b.c.d"

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.update.call_count == 1
    assert document_repo_mock.get.call_count == 0


def test_update_raises_when_invalid_id(document_repo_mock, app_user_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    document.import_id = "invalid"
    updated_doc = create_document_write_dto()
    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, updated_doc, USER_EMAIL)

    expected_msg = f"The import id {document.import_id} is invalid!"
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert app_user_repo_mock.is_superuser.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 0


def test_update_raises_when_invalid_variant(document_repo_mock, app_user_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    document.variant_name = ""
    updated_doc = create_document_write_dto(variant_name="")
    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, updated_doc, USER_EMAIL)

    expected_msg = "Variant name is empty"
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 0
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert app_user_repo_mock.is_superuser.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 0


def test_create_when_no_org_associated_with_entity(
    document_repo_mock, app_user_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto()

    document_repo_mock.no_org = True
    with pytest.raises(ValidationError) as e:
        ok = doc_service.update(document.import_id, updated_doc, USER_EMAIL)
        assert not ok

    expected_msg = "No organisation associated with import id a.b.c.d"
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 0
    assert app_user_repo_mock.is_superuser.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 0


def test_create_when_org_mismatch(document_repo_mock, app_user_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto()

    document_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        ok = doc_service.update(document.import_id, updated_doc, USER_EMAIL)
        assert not ok

    expected_msg = (
        "User 'test@cpr.org' is not authorised to perform operation on 'a.b.c.d'"
    )
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
    assert app_user_repo_mock.is_superuser.call_count == 1
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 0
