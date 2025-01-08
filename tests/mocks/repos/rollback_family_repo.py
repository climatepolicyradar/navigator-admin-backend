from typing import Optional

from pytest import MonkeyPatch
from sqlalchemy.exc import NoResultFound

from app.model.family import FamilyReadDTO


def mock_rollback_family_repo(family_repo, monkeypatch: MonkeyPatch, mocker):
    actual_update = family_repo.update
    actual_create = family_repo.create
    actual_delete = family_repo.delete

    def mock_update_family(
        db, import_id: str, data: FamilyReadDTO, geo_id: int, geo_ids: list[int]
    ) -> Optional[FamilyReadDTO]:
        actual_update(db, import_id, data, geo_id)
        raise NoResultFound()

    def mock_create_family(
        db, data: FamilyReadDTO, geo_id: int, org_id: int
    ) -> Optional[FamilyReadDTO]:
        actual_create(db, data, geo_id, org_id)
        raise NoResultFound()

    def mock_delete_family(db, import_id: str) -> bool:
        actual_delete(db, import_id)
        raise NoResultFound()

    monkeypatch.setattr(family_repo, "update", mock_update_family)
    mocker.spy(family_repo, "update")

    monkeypatch.setattr(family_repo, "create", mock_create_family)
    mocker.spy(family_repo, "create")

    monkeypatch.setattr(family_repo, "delete", mock_delete_family)
    mocker.spy(family_repo, "delete")
