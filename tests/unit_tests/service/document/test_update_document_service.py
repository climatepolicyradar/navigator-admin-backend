import pytest

import app.service.document as doc_service
from app.errors import RepositoryError, ValidationError
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


# --- UPDATE


def test_update(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None

    result = doc_service.update(document.import_id, _to_write_dto(document))
    assert result is not None
    assert document_repo_mock.update.call_count == 1


def test_update_when_missing(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None
    document_repo_mock.return_empty = True

    with pytest.raises(RepositoryError) as e:
        doc_service.update(document.import_id, _to_write_dto(document))
    assert e.value.message == "Error when updating document a.b.c.d"
    assert document_repo_mock.update.call_count == 1


def test_update_raises_when_invalid_id(
    document_repo_mock,
):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document.import_id = "invalid"

    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, _to_write_dto(document))
    expected_msg = f"The import id {document.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert document_repo_mock.update.call_count == 0


def test_update_raises_when_invalid_variant(document_repo_mock):
    document = doc_service.get("a.b.c.d")
    assert document is not None  # needed to placate pyright
    document.variant_name = ""

    with pytest.raises(ValidationError) as e:
        doc_service.update(document.import_id, _to_write_dto(document))
    expected_msg = "Variant name is empty"
    assert e.value.message == expected_msg
    assert document_repo_mock.update.call_count == 0
