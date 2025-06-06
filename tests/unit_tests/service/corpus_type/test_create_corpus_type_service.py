import pytest

import app.service.corpus_type as corpus_type_service
from app.errors import RepositoryError
from tests.helpers.corpus_type import create_corpus_type_create_dto


def test_create(corpus_type_repo_mock):
    new_ct = create_corpus_type_create_dto()
    ct = corpus_type_service.create(new_ct)
    assert ct is not None


def test_create_when_db_fails(corpus_type_repo_mock):
    new_ct = create_corpus_type_create_dto()
    corpus_type_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        corpus_type_service.create(new_ct)
    assert e.value.message == "bad corpus type repo"
    assert corpus_type_repo_mock.create.call_count == 1
