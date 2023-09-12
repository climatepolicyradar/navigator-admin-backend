from typing import Optional
from pytest import MonkeyPatch

from sqlalchemy import exc
from app.model.collection import CollectionDTO


def create_collection_dto(import_id: str) -> CollectionDTO:
    return CollectionDTO(
        import_id=import_id,
        title="title",
        description="description",
        families=[],
        organisation="org",
    )


def mock_collection_repo(collection_repo, monkeypatch: MonkeyPatch, mocker):
    collection_repo.return_empty = False
    collection_repo.throw_repository_error = False

    def maybe_throw():
        if collection_repo.throw_repository_error:
            raise exc.SQLAlchemyError("")

    def mock_get_all(_) -> list[CollectionDTO]:
        return [
            create_collection_dto(import_id="id1"),
            create_collection_dto(import_id="id2"),
            create_collection_dto(import_id="id3"),
        ]

    def mock_get(_, import_id: str) -> Optional[CollectionDTO]:
        return create_collection_dto(import_id=import_id)

    def mock_search(_, q: str) -> list[CollectionDTO]:
        maybe_throw()
        if not collection_repo.return_empty:
            return [create_collection_dto("search1")]
        return []

    def mock_update(_, data: CollectionDTO) -> bool:
        maybe_throw()
        return not collection_repo.return_empty

    def mock_create(_, data: CollectionDTO, __) -> Optional[CollectionDTO]:
        maybe_throw()
        if not collection_repo.return_empty:
            return data

    def mock_delete(_, import_id: str) -> bool:
        maybe_throw()
        return not collection_repo.return_empty

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
