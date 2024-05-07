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


# --- DELETE


def test_delete(collection_repo_mock):
    ok = collection_service.delete("a.b.c.d")
    assert ok
    assert collection_repo_mock.delete.call_count == 1


def test_delete_when_missing(collection_repo_mock):
    collection_repo_mock.return_empty = True
    ok = collection_service.delete("a.b.c.d")
    assert not ok
    assert collection_repo_mock.delete.call_count == 1


def test_delete_raises_when_invalid_id(collection_repo_mock):
    import_id = "invalid"
    with pytest.raises(ValidationError) as e:
        collection_service.delete(import_id)
    expected_msg = f"The import id {import_id} is invalid!"
    assert e.value.message == expected_msg
    assert collection_repo_mock.delete.call_count == 0
