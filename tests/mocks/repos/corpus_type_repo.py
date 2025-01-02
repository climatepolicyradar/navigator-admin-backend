from pytest import MonkeyPatch


def mock_corpus_type_repo(corpus_type_repo, monkeypatch: MonkeyPatch, mocker):
    corpus_type_repo.error = False
    corpus_type_repo.valid = True
