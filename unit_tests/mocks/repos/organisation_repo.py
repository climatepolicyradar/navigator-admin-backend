from typing import Optional
from pytest import MonkeyPatch


def mock_organisation_repo(organisation_repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_id_from_name(_, __) -> Optional[int]:
        if not organisation_repo.error:
            return 1

    organisation_repo.error = False
    monkeypatch.setattr(organisation_repo, "get_id_from_name", mock_get_id_from_name)
    mocker.spy(organisation_repo, "get_id_from_name")
