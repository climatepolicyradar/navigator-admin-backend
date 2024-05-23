from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError
from app.model.collection import CollectionReadDTO, CollectionWriteDTO
from tests.helpers.collection import create_collection_read_dto

ORG_ID = 1
INCORRECT_ORG_ID = 1234


def mock_collection_service(collection_service, monkeypatch: MonkeyPatch, mocker):
    collection_service.missing = False
    collection_service.throw_repository_error = False
    collection_service.throw_timeout_error = False
    collection_service.invalid_org = False
    collection_service.valid = True

    def maybe_throw():
        if collection_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def maybe_timeout():
        if collection_service.throw_timeout_error:
            raise TimeoutError

    def mock_get_all_collections():
        maybe_throw()
        return [create_collection_read_dto("test")]

    def mock_get_collection(import_id: str) -> Optional[CollectionReadDTO]:
        maybe_throw()
        if not collection_service.missing:
            return create_collection_read_dto(import_id)

    def mock_search_collections(q_params: dict) -> list[CollectionReadDTO]:
        maybe_throw()
        maybe_timeout()
        if collection_service.missing:
            return []
        return [create_collection_read_dto("search1")]

    def mock_update_collection(
        import_id: str, data: CollectionWriteDTO
    ) -> Optional[CollectionReadDTO]:
        maybe_throw()
        if not collection_service.missing:
            return create_collection_read_dto(import_id, data.title, data.description)

    def mock_create_collection(data: CollectionWriteDTO, user_email: str) -> str:
        maybe_throw()
        if collection_service.missing:
            raise RepositoryError("missing")
        return "test.new.collection.0"

    def mock_delete_collection(import_id: str) -> bool:
        maybe_throw()
        return not collection_service.missing

    def mock_validate() -> Optional[int]:
        maybe_throw()
        if collection_service.missing is False:
            raise RepositoryError(
                "One or more of the collections to update does not exist"
            )
        return True

    def mock_get_org_from_id() -> Optional[int]:
        maybe_throw()
        if collection_service.missing:
            return None
        if collection_service.invalid_org:
            return INCORRECT_ORG_ID
        return ORG_ID

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

    monkeypatch.setattr(collection_service, "validate", mock_validate)
    mocker.spy(collection_service, "validate")

    monkeypatch.setattr(collection_service, "get_org_from_id", mock_get_org_from_id)
    mocker.spy(collection_service, "get_org_from_id")
