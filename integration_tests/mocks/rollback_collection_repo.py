from typing import Optional
from pytest import MonkeyPatch
from sqlalchemy.exc import NoResultFound

from app.model.collection import CollectionReadDTO


def mock_rollback_collection_repo(collection_repo, monkeypatch: MonkeyPatch, mocker):
    actual_update = collection_repo.update
    actual_create = collection_repo.create
    actual_delete = collection_repo.delete

    def mock_update_collection(
        db, data: CollectionReadDTO
    ) -> Optional[CollectionReadDTO]:
        actual_update(db, data)
        raise NoResultFound()

    def mock_create_collection(
        db, data: CollectionReadDTO, org_id: int
    ) -> Optional[CollectionReadDTO]:
        actual_create(db, data, org_id)
        raise NoResultFound()

    def mock_delete_collection(db, import_id: str) -> bool:
        actual_delete(db, import_id)
        raise NoResultFound()

    monkeypatch.setattr(collection_repo, "update", mock_update_collection)
    mocker.spy(collection_repo, "update")

    monkeypatch.setattr(collection_repo, "create", mock_create_collection)
    mocker.spy(collection_repo, "create")

    monkeypatch.setattr(collection_repo, "delete", mock_delete_collection)
    mocker.spy(collection_repo, "delete")
