from typing import Optional
from pytest import MonkeyPatch

from sqlalchemy import exc
from app.model.family import FamilyReadDTO
from unit_tests.helpers.family import create_family_dto


def mock_family_repo(family_repo, monkeypatch: MonkeyPatch, mocker):
    family_repo.return_empty = False
    family_repo.throw_repository_error = False

    def maybe_throw():
        if family_repo.throw_repository_error:
            raise exc.SQLAlchemyError("")

    def mock_get_all(_):
        return [create_family_dto("test")]

    def mock_get(_, import_id: str) -> Optional[FamilyReadDTO]:
        maybe_throw()
        if not family_repo.return_empty:
            return create_family_dto(import_id)

    def mock_search(_, q: str) -> list[FamilyReadDTO]:
        maybe_throw()
        if not family_repo.return_empty:
            return [create_family_dto("search1")]
        return []

    def mock_update(_, data: FamilyReadDTO, __) -> bool:
        maybe_throw()
        return not family_repo.return_empty

    def mock_create(_, data: FamilyReadDTO, __, ___) -> bool:
        maybe_throw()
        return not family_repo.return_empty

    def mock_delete(_, import_id: str) -> bool:
        maybe_throw()
        return not family_repo.return_empty

    monkeypatch.setattr(family_repo, "get", mock_get)
    mocker.spy(family_repo, "get")

    monkeypatch.setattr(family_repo, "all", mock_get_all)
    mocker.spy(family_repo, "all")

    monkeypatch.setattr(family_repo, "search", mock_search)
    mocker.spy(family_repo, "search")

    monkeypatch.setattr(family_repo, "update", mock_update)
    mocker.spy(family_repo, "update")

    monkeypatch.setattr(family_repo, "create", mock_create)
    mocker.spy(family_repo, "create")

    monkeypatch.setattr(family_repo, "delete", mock_delete)
    mocker.spy(family_repo, "delete")
