from pytest import MonkeyPatch


def mock_validate(_, geo_string: str) -> int:
    return 1


def mock_geography_service(geography_service, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(geography_service, "validate", mock_validate)
    mocker.spy(geography_service, "validate")
