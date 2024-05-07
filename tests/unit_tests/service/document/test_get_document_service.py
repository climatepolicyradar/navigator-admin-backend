import pytest

import app.service.document as doc_service
from app.errors import ValidationError
from app.model.document import DocumentReadDTO, DocumentWriteDTO


def _to_write_dto(dto: DocumentReadDTO) -> DocumentWriteDTO:
    return DocumentWriteDTO(
        variant_name=dto.variant_name,
        role=dto.role,
        type=dto.type,
        title=dto.title,
        source_url=dto.source_url,
        user_language_name=dto.user_language_name,
    )


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


# --- GET


def test_get(document_repo_mock):
    result = doc_service.get("id.1.2.3")
    assert result is not None
    assert result.import_id == "id.1.2.3"
    assert document_repo_mock.get.call_count == 1


def test_get_returns_none(document_repo_mock):
    document_repo_mock.return_empty = True
    result = doc_service.get("id.1.2.3")
    assert result is not None
    assert document_repo_mock.get.call_count == 1


def test_get_raises_when_invalid_id(document_repo_mock):
    with pytest.raises(ValidationError) as e:
        doc_service.get("a.b.c")
    expected_msg = "The import id a.b.c is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.get.call_count == 0
