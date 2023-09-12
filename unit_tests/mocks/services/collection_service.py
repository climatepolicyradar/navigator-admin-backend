from typing import Optional
from pytest import MonkeyPatch

from app.model.collection import CollectionDTO
from unit_tests.helpers.collection import create_collection_dto


def mock_get_all_collections():
    return [create_collection_dto("test")]


def mock_get_collection(import_id: str) -> Optional[CollectionDTO]:
    if import_id == "missing":
        return None
    return create_collection_dto(import_id)


def mock_search_collections(q: str) -> list[CollectionDTO]:
    if q == "empty":
        return []
    else:
        return [create_collection_dto("search1")]


def mock_update_collection(data: CollectionDTO) -> Optional[CollectionDTO]:
    if data.import_id != "missing":
        return data


def mock_create_collection(data: CollectionDTO) -> Optional[CollectionDTO]:
    if data.import_id != "missing":
        return data


def mock_delete_collection(import_id: str) -> bool:
    return import_id != "missing"


def mock_collection_service(collection_service, monkeypatch: MonkeyPatch, mocker):
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
