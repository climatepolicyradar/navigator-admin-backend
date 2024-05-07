import pytest

import app.service.collection as collection_service
from app.errors import RepositoryError
from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)


def _to_write_dto(dto: CollectionReadDTO) -> CollectionWriteDTO:
    return CollectionWriteDTO(
        title=dto.title,
        description=dto.description,
        organisation=dto.organisation,
    )


def _to_create_dto(dto: CollectionReadDTO) -> CollectionCreateDTO:
    return CollectionCreateDTO(
        title=dto.title,
        description=dto.description,
    )


# --- COUNT


def test_count(collection_repo_mock):
    result = collection_service.count()
    assert result is not None
    assert collection_repo_mock.count.call_count == 1


def test_count_returns_none(collection_repo_mock):
    collection_repo_mock.return_empty = True
    result = collection_service.count()
    assert result is None
    assert collection_repo_mock.count.call_count == 1


def test_count_raises_if_db_error(collection_repo_mock):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        collection_service.count()

    expected_msg = "bad repo"
    assert e.value.message == expected_msg
    assert collection_repo_mock.count.call_count == 1
