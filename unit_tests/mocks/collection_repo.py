from typing import Optional
from pytest import MonkeyPatch

from app.model.collection import CollectionDTO


def _create_dto(import_id: str) -> CollectionDTO:
    return CollectionDTO(
        import_id=import_id,
        title="title",
        description="description",
        families=[],
        organisation="org",
    )


def mock_collection_repo(collection_repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_all(_) -> list[CollectionDTO]:
        return [
            _create_dto(import_id="id1"),
            _create_dto(import_id="id2"),
            _create_dto(import_id="id3"),
        ]

    def mock_get(_, import_id: str) -> Optional[CollectionDTO]:
        return _create_dto(import_id=import_id)

    # collection_repo.error = False
    monkeypatch.setattr(collection_repo, "all", mock_get_all)
    monkeypatch.setattr(collection_repo, "get", mock_get)
    mocker.spy(collection_repo, "all")
    mocker.spy(collection_repo, "get")
