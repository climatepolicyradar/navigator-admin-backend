from typing import Optional
from pytest import MonkeyPatch

from sqlalchemy import exc
from app.model.family import FamilyDTO
from unit_tests.helpers.family import create_family_dto


def mock_family_repo(family_repo, monkeypatch: MonkeyPatch, mocker):
    family_repo.error = False
    family_repo.throw_repository_error = False

    def maybe_throw():
        if family_repo.throw_repository_error:
            raise exc.SQLAlchemyError("")

    def mock_get_all_families(_):
        return [create_family_dto("test")]

    def mock_get_family(_, import_id: str) -> Optional[FamilyDTO]:
        maybe_throw()
        if not family_repo.error:
            return create_family_dto(import_id)

    def mock_search_families(_, q: str) -> list[FamilyDTO]:
        maybe_throw()
        if not family_repo.error:
            return [create_family_dto("search1")]
        return []

    def mock_update_family(_, data: FamilyDTO, __) -> bool:
        maybe_throw()
        return not family_repo.error

    def mock_create_family(_, data: FamilyDTO, __, ___) -> Optional[FamilyDTO]:
        maybe_throw()
        if not family_repo.error:
            return data

    def mock_delete_family(_, import_id: str) -> bool:
        maybe_throw()
        return not family_repo.error

    monkeypatch.setattr(family_repo, "get", mock_get_family)
    mocker.spy(family_repo, "get")

    monkeypatch.setattr(family_repo, "all", mock_get_all_families)
    mocker.spy(family_repo, "all")

    monkeypatch.setattr(family_repo, "search", mock_search_families)
    mocker.spy(family_repo, "search")

    monkeypatch.setattr(family_repo, "update", mock_update_family)
    mocker.spy(family_repo, "update")

    monkeypatch.setattr(family_repo, "create", mock_create_family)
    mocker.spy(family_repo, "create")

    monkeypatch.setattr(family_repo, "delete", mock_delete_family)
    mocker.spy(family_repo, "delete")
