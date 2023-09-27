from typing import Optional
from pytest import MonkeyPatch
from app.errors import RepositoryError

from app.model.document import DocumentReadDTO, DocumentWriteDTO
from unit_tests.helpers.document import create_document_dto


def mock_document_service(document_service, monkeypatch: MonkeyPatch, mocker):
    document_service.missing = False
    document_service.throw_repository_error = False

    def maybe_throw():
        if document_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_get_all_documents() -> list[DocumentReadDTO]:
        maybe_throw()
        return [create_document_dto("test")]

    def mock_get_document(import_id: str) -> Optional[DocumentReadDTO]:
        maybe_throw()
        if not document_service.missing:
            return create_document_dto(import_id)

    def mock_search_documents(q: str) -> list[DocumentReadDTO]:
        maybe_throw()
        if document_service.missing:
            return []
        else:
            return [create_document_dto("search1")]

    def mock_update_document(data: DocumentWriteDTO) -> Optional[DocumentReadDTO]:
        maybe_throw()
        if not document_service.missing:
            return create_document_dto(data.import_id, "family_import_id", data.title)

    def mock_create_document(data: DocumentReadDTO) -> Optional[DocumentReadDTO]:
        maybe_throw()
        if not document_service.missing:
            return create_document_dto(
                data.import_id, data.family_import_id, data.title
            )

    def mock_delete_document(_) -> bool:
        maybe_throw()
        return not document_service.missing

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
