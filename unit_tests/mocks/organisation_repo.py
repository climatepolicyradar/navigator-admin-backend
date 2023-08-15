from typing import Optional
from pytest import MonkeyPatch


def mock_get_id_from_name(_, org_name: str) -> Optional[int]:
    if org_name != "Invalid":
        return 1


def mock_organisation_repo(organisation_service, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(organisation_service, "get_id_from_name", mock_get_id_from_name)
    mocker.spy(organisation_service, "get_id_from_name")
