import pytest
from app.errors import ValidationError
from app.model.collection import CollectionReadDTO, CollectionWriteDTO
import app.service.collection as collection_service
from unit_tests.mocks.repos.collection_repo import create_collection_dto as create_dto


def _to_write_dto(dto: CollectionReadDTO) -> CollectionWriteDTO:
    return CollectionWriteDTO(
        import_id=dto.import_id,
        title=dto.title,
        description=dto.description,
        organisation=dto.organisation,
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
    result = collection_service.search("two")
    assert result is not None
    assert len(result) == 1
    assert collection_repo_mock.search.call_count == 1


def test_search_when_missing(collection_repo_mock):
    collection_repo_mock.return_empty = True
    result = collection_service.search("empty")
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

    result = collection_service.update(_to_write_dto(collection))
    assert result is not None
    assert collection_repo_mock.update.call_count == 1


def test_update_when_missing(
    collection_repo_mock,
):
    collection = collection_service.get("a.b.c.d")
    assert collection is not None
    collection_repo_mock.return_empty = True

    result = collection_service.update(_to_write_dto(collection))
    assert result is None
    assert collection_repo_mock.update.call_count == 1


def test_update_raises_when_invalid_id(
    collection_repo_mock,
):
    collection = collection_service.get("a.b.c.d")
    assert collection is not None  # needed to placate pyright
    collection.import_id = "invalid"

    with pytest.raises(ValidationError) as e:
        collection_service.update(_to_write_dto(collection))
    expected_msg = f"The import id {collection.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert collection_repo_mock.update.call_count == 0


# --- CREATE


def test_create(
    collection_repo_mock,
    organisation_repo_mock,
):
    new_collection = create_dto(import_id="A.0.0.5")
    collection = collection_service.create(_to_write_dto(new_collection))
    assert collection is not None
    assert collection_repo_mock.create.call_count == 1
    # Ensure the collection service uses the org service to validate
    assert organisation_repo_mock.get_id_from_name.call_count == 1


def test_create_when_db_fails(
    collection_repo_mock,
    organisation_repo_mock,
):
    new_collection = create_dto(import_id="a.b.c.d")
    collection_repo_mock.return_empty = True
    collection = collection_service.create(_to_write_dto(new_collection))
    assert collection is None
    assert collection_repo_mock.create.call_count == 1
    # Ensure the collection service uses the geo service to validate
    assert organisation_repo_mock.get_id_from_name.call_count == 1


def test_create_raises_when_invalid_id(collection_repo_mock):
    new_collection = create_dto(import_id="invalid")
    with pytest.raises(ValidationError) as e:
        collection_service.create(_to_write_dto(new_collection))
    expected_msg = f"The import id {new_collection.import_id} is invalid!"
    assert e.value.message == expected_msg
    assert collection_repo_mock.create.call_count == 0
