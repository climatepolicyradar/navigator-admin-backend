from typing import Optional

from pytest import MonkeyPatch


def mock_geography_repo(geography_repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_id_from_value(_, __) -> Optional[int]:
        if not geography_repo.error:
            return 1

    geography_repo.error = False
    monkeypatch.setattr(geography_repo, "get_id_from_value", mock_get_id_from_value)
    mocker.spy(geography_repo, "get_id_from_value")
