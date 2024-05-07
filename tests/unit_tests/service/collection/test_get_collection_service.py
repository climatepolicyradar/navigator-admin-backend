import pytest

import app.service.collection as collection_service
from app.errors import ValidationError
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


# --- GET


def test_get(collection_repo_mock):
    result = collection_service.get("id.1.2.3")
    assert result is not None
    assert result.import_id == "id.1.2.3"
    assert collection_repo_mock.get.call_count == 1


def test_get_returns_none(collection_repo_mock):
    collection_repo_mock.return_empty = True
    result = collection_service.get("id.1.2.3")
    assert result is not None
    assert collection_repo_mock.get.call_count == 1


def test_get_raises_if_invalid_id(collection_repo_mock):
    with pytest.raises(ValidationError) as e:
        collection_service.get("a.b.c")
    expected_msg = "The import id a.b.c is invalid!"
    assert e.value.message == expected_msg
    assert collection_repo_mock.get.call_count == 0
