import app.service.corpus_type as corpus_type_service


def test_get(corpus_type_repo_mock):
    result = corpus_type_service.get("some_corpus_type_name")
    assert result is not None
    assert result.name == "test_name"
    assert corpus_type_repo_mock.get.call_count == 1


def test_get_returns_none(corpus_type_repo_mock):
    corpus_type_repo_mock.return_empty = True
    result = corpus_type_service.get("some_corpus_type_name")
    assert result is None
    assert corpus_type_repo_mock.get.call_count == 1
