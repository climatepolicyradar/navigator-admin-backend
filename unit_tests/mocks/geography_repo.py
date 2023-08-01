from typing import Optional
from pytest import MonkeyPatch

INVALID_GEO_VALUE = "UK"


def mock_get_id_from_value(_, geo_string: str) -> Optional[int]:
    if geo_string != INVALID_GEO_VALUE:
        return 1


def mock_geography_repo(geography_repo, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(geography_repo, "get_id_from_value", mock_get_id_from_value)
    mocker.spy(geography_repo, "get_id_from_value")
