from typing import Optional
from pytest import MonkeyPatch
from sqlalchemy.exc import NoResultFound

from app.model.document import DocumentCreateDTO, DocumentReadDTO


def mock_rollback_document_repo(document_repo, monkeypatch: MonkeyPatch, mocker):
    actual_update = document_repo.update
    actual_create = document_repo.create
    actual_delete = document_repo.delete

    def mock_update_document(
        db, import_id: str, data: DocumentReadDTO
    ) -> Optional[DocumentReadDTO]:
        actual_update(db, import_id, data)
        raise NoResultFound()

    def mock_create_document(db, data: DocumentCreateDTO) -> Optional[DocumentReadDTO]:
        actual_create(db, data)
        raise NoResultFound()

    def mock_delete_document(db, import_id: str) -> bool:
        actual_delete(db, import_id)
        raise NoResultFound()

    monkeypatch.setattr(document_repo, "update", mock_update_document)
    mocker.spy(document_repo, "update")

    monkeypatch.setattr(document_repo, "create", mock_create_document)
    mocker.spy(document_repo, "create")

    monkeypatch.setattr(document_repo, "delete", mock_delete_document)
    mocker.spy(document_repo, "delete")
