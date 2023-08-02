from pytest import MonkeyPatch


def mock_validate(_, geo_string: str) -> int:
    return 1


def mock_organisation_service(organisation_service, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(organisation_service, "validate", mock_validate)
    mocker.spy(organisation_service, "validate")
