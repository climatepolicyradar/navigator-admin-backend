from typing import Optional
from pytest import MonkeyPatch
from sqlalchemy.exc import NoResultFound

from app.model.family import FamilyDTO


def mock_rollback_family_repo(family_repo, monkeypatch: MonkeyPatch, mocker):
    actual_update = family_repo.update

    def mock_update_family(db, data: FamilyDTO) -> Optional[FamilyDTO]:
        actual_update(db, data)
        raise NoResultFound()

    # def mock_create_family(db, data: FamilyDTO) -> Optional[FamilyDTO]:
    #     actual_family_repo.create(db, data)
    #     raise NoResultFound()

    # def mock_delete_family(db, import_id: str) -> bool:
    #     actual_family_repo.create(db, import_id)
    #     raise NoResultFound()

    monkeypatch.setattr(family_repo, "update", mock_update_family)
    mocker.spy(family_repo, "update")

    # monkeypatch.setattr(family_repo, "create", mock_create_family)
    # mocker.spy(family_repo, "create")

    # monkeypatch.setattr(family_repo, "delete", mock_delete_family)
    # mocker.spy(family_repo, "delete")
