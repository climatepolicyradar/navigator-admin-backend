import pytest
from tests.helpers.collection import create_collection_write_dto

import app.service.collection as collection_service
from app.errors import RepositoryError, ValidationError


def test_update(collection_repo_mock):
    collection = collection_service.get("a.b.c.d")
    assert collection is not None

    updated_collection = create_collection_write_dto()
    result = collection_service.update("a.b.c.d", updated_collection)
    assert result is not None
    assert collection_repo_mock.update.call_count == 1


def test_update_when_missing(collection_repo_mock):
    collection = create_collection_write_dto()
    assert collection is not None
    collection_repo_mock.return_empty = True

    with pytest.raises(RepositoryError) as e:
        collection_service.update("a.b.c.d", collection)

    assert collection_repo_mock.update.call_count == 1
    expected_msg = "app.service.collection::update('a.b.c.d', CollectionWriteDTO(title='title', description='description', organisation='CCLW', metadata={}))"
    assert e.value.message == expected_msg


def test_update_raises_when_invalid_id(collection_repo_mock):
    collection = create_collection_write_dto()

    with pytest.raises(ValidationError) as e:
        collection_service.update("invalid", collection)
    expected_msg = "The import id invalid is invalid!"
    assert e.value.message == expected_msg
    assert collection_repo_mock.update.call_count == 0
