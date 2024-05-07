import pytest

import app.service.document as doc_service
from app.errors import RepositoryError, ValidationError
from tests.helpers.document import create_document_create_dto


def test_document_service_get_upload_details(test_s3_client):
    result = doc_service.get_upload_details("path/file.ext", True)
    assert result is not None
    assert len(result) == 2
    # Check the signed url starts with the right path
    assert result[0].startswith(
        "https://test-document-bucket.s3.amazonaws.com/path/file.ext?"
    )
    assert "X-Amz-Algorithm" in result[0]
    assert "X-Amz-Credential" in result[0]
    assert "X-Amz-Date" in result[0]
    assert "X-Amz-Expires=3600" in result[0]
    assert "X-Amz-Signature" in result[0]

    assert result[1] == "https://cdn.climatepolicyradar.org/path/file.ext"


# --- CREATE


def test_create(document_repo_mock, family_repo_mock):
    new_document = create_document_create_dto()
    document = doc_service.create(new_document)
    assert document is not None
    assert document_repo_mock.create.call_count == 1
    assert family_repo_mock.get.call_count == 1


def test_create_when_db_fails(document_repo_mock, family_repo_mock):
    new_document = create_document_create_dto()
    document_repo_mock.return_empty = True

    with pytest.raises(RepositoryError):
        doc_service.create(new_document)
    assert document_repo_mock.create.call_count == 1
    assert family_repo_mock.get.call_count == 1


def test_create_raises_when_invalid_family_id(document_repo_mock):
    new_document = create_document_create_dto(family_import_id="invalid family")
    with pytest.raises(ValidationError) as e:
        doc_service.create(new_document)
    expected_msg = f"The import id {new_document.family_import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.create.call_count == 0


def test_create_raises_when_blank_variant(document_repo_mock):
    new_document = create_document_create_dto(variant_name="")
    with pytest.raises(ValidationError) as e:
        doc_service.create(new_document)
    expected_msg = "Variant name is empty"
    assert e.value.message == expected_msg
    assert document_repo_mock.create.call_count == 0
