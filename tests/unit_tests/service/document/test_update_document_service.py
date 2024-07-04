import pytest

import app.service.document as doc_service
from app.errors import AuthorisationError, ValidationError
from tests.helpers.document import create_document_write_dto


def test_update(
    document_repo_mock, admin_user_context, family_repo_mock, corpus_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto(metadata={"color": ["pink"], "size": [0]})
    result = doc_service.update(document.import_id, updated_doc, admin_user_context)
    assert result is not None

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert document_repo_mock.update.call_count == 1
    assert document_repo_mock.get.call_count == 2


def test_update_when_missing(
    document_repo_mock, admin_user_context, family_repo_mock, corpus_repo_mock
):
    document_repo_mock.return_empty = True
    updated_doc = create_document_write_dto()
    result = doc_service.update("w.x.y.z", updated_doc, admin_user_context)
    assert result is None

    assert document_repo_mock.get_org_from_import_id.call_count == 0
    assert family_repo_mock.get.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 1


def test_update_raises_when_invalid_id(
    document_repo_mock, admin_user_context, family_repo_mock, corpus_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    document.import_id = "invalid"
    updated_doc = create_document_write_dto()
    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, updated_doc, admin_user_context)

    expected_msg = f"The import id {document.import_id} is invalid!"
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 0
    assert family_repo_mock.get.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 0


def test_update_raises_when_invalid_variant(
    document_repo_mock, admin_user_context, family_repo_mock, corpus_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    document.variant_name = ""
    updated_doc = create_document_write_dto(variant_name="")
    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, updated_doc, admin_user_context)

    expected_msg = "Variant name is empty"
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 0
    assert family_repo_mock.get.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 1


def test_update_document_raises_when_metadata_invalid(
    document_repo_mock, admin_user_context, family_repo_mock, corpus_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto(metadata={"invalid": True})
    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, updated_doc, admin_user_context)

    expected_message = "Metadata validation failed: "
    expected_missing_message = "Missing metadata keys: {'size', 'color'}"
    expected_extra_message = "Extra metadata keys: {'invalid'}"

    assert e.value.message.startswith(expected_message)
    assert len(e.value.message) == len(
        expected_message + expected_missing_message + "," + expected_extra_message
    )

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 1


def test_update_when_no_org_associated_with_entity(
    document_repo_mock, admin_user_context, family_repo_mock, corpus_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto()

    document_repo_mock.no_org = True
    with pytest.raises(ValidationError) as e:
        ok = doc_service.update(document.import_id, updated_doc, admin_user_context)
        assert not ok

    expected_msg = "No organisation associated with import id a.b.c.d"
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert family_repo_mock.get.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 1


def test_update_raises_when_org_mismatch(
    document_repo_mock, another_admin_user_context, family_repo_mock, corpus_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto()

    document_repo_mock.alternative_org = True
    with pytest.raises(AuthorisationError) as e:
        ok = doc_service.update(
            document.import_id, updated_doc, another_admin_user_context
        )
        assert not ok

    expected_msg = "User 'another-admin@here.com' is not authorised to perform operation on 'a.b.c.d'"
    assert e.value.message == expected_msg

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert family_repo_mock.get.call_count == 0
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 0
    assert document_repo_mock.update.call_count == 0
    assert document_repo_mock.get.call_count == 1


def test_update_success_when_org_mismatch_superuser(
    document_repo_mock, super_user_context, family_repo_mock, corpus_repo_mock
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.get.call_count = 0
    assert document_repo_mock.get.call_count == 0

    updated_doc = create_document_write_dto(metadata={"color": ["pink"], "size": [0]})

    result = doc_service.update(document.import_id, updated_doc, super_user_context)
    assert result is not None

    assert document_repo_mock.get_org_from_import_id.call_count == 1
    assert family_repo_mock.get.call_count == 1
    assert corpus_repo_mock.get_taxonomy_from_corpus.call_count == 1
    assert document_repo_mock.update.call_count == 1
    assert document_repo_mock.get.call_count == 2
