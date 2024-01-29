import pytest

import app.service.collection as collection_service
from db_client.errors import RepositoryError, ValidationError
from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)
from unit_tests.helpers.collection import create_collection_write_dto
from unit_tests.mocks.repos.collection_repo import (
    create_collection_read_dto as create_dto,
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


# --- SEARCH


def test_search(collection_repo_mock):
    result = collection_service.search({"q": "two"})
    assert result is not None
    assert len(result) == 1
    assert collection_repo_mock.search.call_count == 1


def test_search_db_error(collection_repo_mock):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        collection_service.search({"q": "error"})
    assert collection_repo_mock.search.call_count == 1


def test_search_request_timeout(collection_repo_mock):
    collection_repo_mock.throw_timeout_error = True
    with pytest.raises(TimeoutError):
        collection_service.search({"q": "timeout"})
    assert collection_repo_mock.search.call_count == 1


def test_search_missing(collection_repo_mock):
    collection_repo_mock.return_empty = True
    result = collection_service.search({"q": "empty"})
    assert result is not None
    assert len(result) == 0
    assert collection_repo_mock.search.call_count == 1


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


# --- UPDATE


def test_update(
    collection_repo_mock,
):
    collection = collection_service.get("a.b.c.d")
    assert collection is not None

    result = collection_service.update("a.b.c.d", _to_write_dto(collection))
    assert result is not None
    assert collection_repo_mock.update.call_count == 1


def test_update_when_missing(
    collection_repo_mock,
):
    collection = create_collection_write_dto()
    assert collection is not None
    collection_repo_mock.return_empty = True

    with pytest.raises(RepositoryError) as e:
        collection_service.update("a.b.c.d", collection)

    assert collection_repo_mock.update.call_count == 1
    expected_msg = "Error when updating collection 'a.b.c.d'"
    assert e.value.message == expected_msg


def test_update_raises_when_invalid_id(
    collection_repo_mock,
):
    collection = create_collection_write_dto()

    with pytest.raises(ValidationError) as e:
        collection_service.update("invalid", collection)
    expected_msg = "The import id invalid is invalid!"
    assert e.value.message == expected_msg
    assert collection_repo_mock.update.call_count == 0


# --- CREATE

USER_EMAIL = "test@cpr.org"


def test_create(
    collection_repo_mock,
    app_user_repo_mock,
):
    new_collection = create_dto(import_id="A.0.0.5")
    collection = collection_service.create(_to_create_dto(new_collection), USER_EMAIL)
    assert collection is not None
    assert collection_repo_mock.create.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1


def test_create_when_db_fails(
    collection_repo_mock,
    app_user_repo_mock,
):
    new_collection = create_dto(import_id="a.b.c.d")
    collection_repo_mock.return_empty = True
    with pytest.raises(RepositoryError) as e:
        collection_service.create(_to_create_dto(new_collection), USER_EMAIL)
    assert e.value.message == "Error when creating collection 'description'"
    assert collection_repo_mock.create.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1


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
