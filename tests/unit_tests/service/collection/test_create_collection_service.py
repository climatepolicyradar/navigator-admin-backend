import pytest

import app.service.collection as collection_service
from app.errors import RepositoryError
from tests.helpers.collection import create_collection_create_dto

# --- CREATE


def test_create(collection_repo_mock, app_user_repo_mock, admin_user_context):
    new_collection = create_collection_create_dto()
    collection = collection_service.create(new_collection, admin_user_context)
    assert collection is not None
    assert collection_repo_mock.create.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1


def test_create_when_db_fails(
    collection_repo_mock, app_user_repo_mock, admin_user_context
):
    new_collection = create_collection_create_dto()
    collection_repo_mock.return_empty = True
    with pytest.raises(RepositoryError) as e:
        collection_service.create(new_collection, admin_user_context)
    assert e.value.message == "Error when creating collection 'description'"
    assert collection_repo_mock.create.call_count == 1
    assert app_user_repo_mock.get_org_id.call_count == 1
