import pytest

import app.service.collection as collection_service
from app.errors import RepositoryError
from app.model.collection import (
    CollectionCreateDTO,
    CollectionReadDTO,
    CollectionWriteDTO,
)
from tests.mocks.repos.collection_repo import create_collection_read_dto as create_dto


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
