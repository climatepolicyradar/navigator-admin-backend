from typing import Optional
from pytest import MonkeyPatch

from app.model.collection import CollectionReadDTO, CollectionWriteDTO
from unit_tests.helpers.collection import create_collection_dto


def mock_collection_service(collection_service, monkeypatch: MonkeyPatch, mocker):
    collection_service.missing = False

    def mock_get_all_collections():
        return [create_collection_dto("test")]

    def mock_get_collection(import_id: str) -> Optional[CollectionReadDTO]:
        if not collection_service.missing:
            return create_collection_dto(import_id)

    def mock_search_collections(q: str) -> list[CollectionReadDTO]:
        if q == "empty":
            return []
        else:
            return [create_collection_dto("search1")]

    def mock_update_collection(data: CollectionWriteDTO) -> Optional[CollectionReadDTO]:
        if not collection_service.missing:
            return create_collection_dto(data.import_id, data.title, data.description)

    def mock_create_collection(data: CollectionWriteDTO) -> Optional[CollectionReadDTO]:
        if not collection_service.missing:
            return create_collection_dto(data.import_id, data.title, data.description)

    def mock_delete_collection(import_id: str) -> bool:
        return not collection_service.missing

    monkeypatch.setattr(collection_service, "get", mock_get_collection)
    mocker.spy(collection_service, "get")

    monkeypatch.setattr(collection_service, "all", mock_get_all_collections)
    mocker.spy(collection_service, "all")

    monkeypatch.setattr(collection_service, "search", mock_search_collections)
    mocker.spy(collection_service, "search")

    monkeypatch.setattr(collection_service, "update", mock_update_collection)
    mocker.spy(collection_service, "update")

    monkeypatch.setattr(collection_service, "create", mock_create_collection)
    mocker.spy(collection_service, "create")

    monkeypatch.setattr(collection_service, "delete", mock_delete_collection)
    mocker.spy(collection_service, "delete")
