from typing import Optional

from pytest import MonkeyPatch
from sqlalchemy import exc

from app.errors import RepositoryError
from app.model.document import DocumentCreateDTO, DocumentReadDTO
from tests.helpers.document import create_document_read_dto


def mock_document_repo(document_repo, monkeypatch: MonkeyPatch, mocker):
    document_repo.return_empty = False
    document_repo.throw_repository_error = False
    document_repo.throw_timeout_error = False
    document_repo.is_superuser = False

    def maybe_throw():
        if document_repo.throw_repository_error:
            raise RepositoryError("bad document repo")

    def maybe_timeout():
        if document_repo.throw_timeout_error:
            raise TimeoutError

    def mock_get_all(_, org_id: Optional[int]) -> list[DocumentReadDTO]:
        maybe_throw()
        values = []
        for x in range(3):
            dto = create_document_read_dto(import_id=f"id{x}")
            values.append(dto)
        return values

    def mock_get(_, import_id: str) -> Optional[DocumentReadDTO]:
        dto = create_document_read_dto(import_id)
        return dto

    def mock_search(_, q: str, org_id: Optional[int]) -> list[DocumentReadDTO]:
        maybe_throw()
        maybe_timeout()
        if not document_repo.return_empty:
            return [create_document_read_dto("search1")]
        return []

    def mock_update(_, import_id: str, data: DocumentReadDTO) -> DocumentReadDTO:
        maybe_throw()
        if document_repo.return_empty:
            raise exc.NoResultFound()
        return create_document_read_dto("a.b.c.d")

    def mock_create(_, data: DocumentCreateDTO) -> str:
        maybe_throw()
        if document_repo.return_empty:
            raise exc.NoResultFound()
        return "test.new.doc.0"

    def mock_delete(_, import_id: str) -> bool:
        maybe_throw()
        return not document_repo.return_empty

    def mock_get_count(_, org_id: Optional[int]) -> Optional[int]:
        maybe_throw()
        if not document_repo.return_empty:
            if document_repo.is_superuser:
                return 33
            return 11
        return

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

    monkeypatch.setattr(document_repo, "count", mock_get_count)
    mocker.spy(document_repo, "count")
