from typing import Optional
from pytest import MonkeyPatch

from sqlalchemy import exc
from app.errors import RepositoryError
from app.model.document import DocumentCreateDTO, DocumentReadDTO
from unit_tests.helpers.document import create_document_read_dto


def mock_document_repo(document_repo, monkeypatch: MonkeyPatch, mocker):
    document_repo.return_empty = False
    document_repo.throw_repository_error = False

    def maybe_throw():
        if document_repo.throw_repository_error:
            raise exc.SQLAlchemyError("")

    def mock_get_all(_) -> list[DocumentReadDTO]:
        values = []
        for x in range(3):
            dto = create_document_read_dto(import_id=f"id{x}")
            values.append(dto)
        return values

    def mock_get(_, import_id: str) -> Optional[DocumentReadDTO]:
        dto = create_document_read_dto(import_id)
        return dto

    def mock_search(_, q: str) -> list[DocumentReadDTO]:
        maybe_throw()
        if not document_repo.return_empty:
            return [create_document_read_dto("search1")]
        return []

    def mock_update(_, data: DocumentReadDTO) -> bool:
        maybe_throw()
        return not document_repo.return_empty

    def mock_create(_, data: DocumentCreateDTO) -> str:
        maybe_throw()
        if document_repo.return_empty:
            raise RepositoryError("testing error")
        return "test.new.doc.0  "

    def mock_delete(_, import_id: str) -> bool:
        maybe_throw()
        return not document_repo.return_empty

    monkeypatch.setattr(document_repo, "get", mock_get)
    mocker.spy(document_repo, "get")

    monkeypatch.setattr(document_repo, "all", mock_get_all)
    mocker.spy(document_repo, "all")

    monkeypatch.setattr(document_repo, "search", mock_search)
    mocker.spy(document_repo, "search")

    monkeypatch.setattr(document_repo, "update", mock_update)
    mocker.spy(document_repo, "update")

    monkeypatch.setattr(document_repo, "create", mock_create)
    mocker.spy(document_repo, "create")

    monkeypatch.setattr(document_repo, "delete", mock_delete)
    mocker.spy(document_repo, "delete")
