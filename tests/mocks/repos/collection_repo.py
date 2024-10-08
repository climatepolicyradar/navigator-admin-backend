from typing import Optional

from pytest import MonkeyPatch
from sqlalchemy import exc

from app.errors import RepositoryError
from app.model.collection import CollectionReadDTO
from tests.helpers.collection import create_collection_read_dto

STANDARD_ORG_ID = 1
ALTERNATIVE_ORG_ID = 999


def mock_collection_repo(collection_repo, monkeypatch: MonkeyPatch, mocker):
    collection_repo.return_empty = False
    collection_repo.missing = False
    collection_repo.throw_repository_error = False
    collection_repo.throw_timeout_error = False
    collection_repo.alternative_org = False
    collection_repo.is_superuser = False

    def maybe_throw():
        if collection_repo.throw_repository_error:
            raise RepositoryError("bad collection repo")

    def maybe_timeout():
        if collection_repo.throw_timeout_error:
            raise TimeoutError

    def mock_get_all(_, org_id: Optional[int]) -> list[CollectionReadDTO]:
        maybe_throw()
        if collection_repo.return_empty:
            return []
        return [
            create_collection_read_dto(import_id="id1"),
            create_collection_read_dto(import_id="id2"),
            create_collection_read_dto(import_id="id3"),
        ]

    def mock_get(_, import_id: str) -> Optional[CollectionReadDTO]:
        return create_collection_read_dto(import_id=import_id)

    def mock_search(_, q: str, org_id: Optional[int]) -> list[CollectionReadDTO]:
        maybe_throw()
        maybe_timeout()
        if not collection_repo.return_empty:
            return [create_collection_read_dto("search1")]
        return []

    def mock_update(_, import_id: str, data: CollectionReadDTO) -> CollectionReadDTO:
        maybe_throw()
        if collection_repo.return_empty:
            raise exc.NoResultFound()
        return create_collection_read_dto("a.b.c.d")

    def mock_create(_, data: CollectionReadDTO, __) -> str:
        maybe_throw()
        if collection_repo.return_empty:
            raise exc.NoResultFound()
        return data.import_id if data.import_id else "test.new.collection.0"

    def mock_delete(_, import_id: str) -> bool:
        maybe_throw()
        return not collection_repo.return_empty

    def mock_get_count(_, org_id: Optional[int]) -> Optional[int]:
        maybe_throw()
        if collection_repo.return_empty is False:
            if collection_repo.is_superuser:
                return 11
            return 5
        return

    def mock_validate(_, __) -> bool:
        maybe_throw()
        if collection_repo.missing:
            return False
        return True

    def mock_get_org_from_collection_id(_, import_id: str) -> Optional[int]:
        maybe_throw()
        if collection_repo.missing is True:
            return None
        if collection_repo.alternative_org is True:
            return ALTERNATIVE_ORG_ID
        return STANDARD_ORG_ID

    monkeypatch.setattr(collection_repo, "get", mock_get)
    mocker.spy(collection_repo, "get")

    monkeypatch.setattr(collection_repo, "all", mock_get_all)
    mocker.spy(collection_repo, "all")

    monkeypatch.setattr(collection_repo, "search", mock_search)
    mocker.spy(collection_repo, "search")

    monkeypatch.setattr(collection_repo, "update", mock_update)
    mocker.spy(collection_repo, "update")

    monkeypatch.setattr(collection_repo, "create", mock_create)
    mocker.spy(collection_repo, "create")

    monkeypatch.setattr(collection_repo, "delete", mock_delete)
    mocker.spy(collection_repo, "delete")

    monkeypatch.setattr(collection_repo, "count", mock_get_count)
    mocker.spy(collection_repo, "count")

    monkeypatch.setattr(collection_repo, "validate", mock_validate)
    mocker.spy(collection_repo, "validate")

    monkeypatch.setattr(
        collection_repo, "get_org_from_collection_id", mock_get_org_from_collection_id
    )
    mocker.spy(collection_repo, "get_org_from_collection_id")
