from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
from tests.helpers.document import create_document_read_dto


def mock_document_service(document_service, monkeypatch: MonkeyPatch, mocker):
    document_service.missing = False
    document_service.throw_repository_error = False
    document_service.throw_validation_error = False
    document_service.throw_timeout_error = False

    def maybe_throw():
        if document_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def maybe_timeout():
        if document_service.throw_timeout_error:
            raise TimeoutError

    def mock_get_all_documents() -> list[DocumentReadDTO]:
        maybe_throw()
        return [create_document_read_dto("test")]

    def mock_get_document(import_id: str) -> Optional[DocumentReadDTO]:
        maybe_throw()
        if not document_service.missing:
            return create_document_read_dto(import_id)

    def mock_search_documents(q_params: dict) -> list[DocumentReadDTO]:
        if document_service.missing:
            return []

        maybe_throw()
        maybe_timeout()
        return [create_document_read_dto("search1")]

    def mock_update_document(
        import_id: str, data: DocumentWriteDTO
    ) -> Optional[DocumentReadDTO]:
        maybe_throw()
        if document_service.missing:
            return

        if document_service.throw_validation_error:
            raise ValidationError("Variant name is empty")

        return create_document_read_dto(import_id, "family_import_id", data.title)

    def mock_create_document(data: DocumentCreateDTO) -> str:
        maybe_throw()
        if document_service.throw_validation_error:
            raise ValidationError("Variant name is empty")

        if document_service.missing:
            raise ValidationError(f"Could not find family for {data.family_import_id}")
        return "new.doc.id.0"

    def mock_delete_document(_) -> bool:
        maybe_throw()
        return not document_service.missing

    def mock_count_collection() -> Optional[int]:
        maybe_throw()
        if document_service.missing:
            return None
        return 33

    monkeypatch.setattr(document_service, "get", mock_get_document)
    mocker.spy(document_service, "get")

    monkeypatch.setattr(document_service, "all", mock_get_all_documents)
    mocker.spy(document_service, "all")

    monkeypatch.setattr(document_service, "search", mock_search_documents)
    mocker.spy(document_service, "search")

    monkeypatch.setattr(document_service, "update", mock_update_document)
    mocker.spy(document_service, "update")

    monkeypatch.setattr(document_service, "create", mock_create_document)
    mocker.spy(document_service, "create")

    monkeypatch.setattr(document_service, "delete", mock_delete_document)
    mocker.spy(document_service, "delete")

    monkeypatch.setattr(document_service, "count", mock_count_collection)
    mocker.spy(document_service, "count")
