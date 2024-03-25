from pytest import MonkeyPatch

from app.repository.protocols import FamilyRepo

from . import family_repo as mock_repo

mock_repo: FamilyRepo


def create_mock_family_repo(family_repo, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(family_repo, "get", mock_repo.get)
    mocker.spy(family_repo, "get")

    monkeypatch.setattr(family_repo, "all", mock_repo.all)
    mocker.spy(family_repo, "all")

    monkeypatch.setattr(family_repo, "search", mock_repo.search)
    mocker.spy(family_repo, "search")

    monkeypatch.setattr(family_repo, "update", mock_repo.update)
    mocker.spy(family_repo, "update")

    monkeypatch.setattr(family_repo, "create", mock_repo.create)
    mocker.spy(family_repo, "create")

    monkeypatch.setattr(family_repo, "delete", mock_repo.delete)
    mocker.spy(family_repo, "delete")

    monkeypatch.setattr(family_repo, "count", mock_repo.count)
    mocker.spy(family_repo, "count")
