from pytest import MonkeyPatch

ORG_ID = 1234


def mock_app_user_service(app_user_service, monkeypatch: MonkeyPatch, mocker):
    app_user_service.invalid_org = False

    def mock_get_organisation(_, user_email: str) -> int:
        if app_user_service.invalid_org is True:
            return ORG_ID
        return 1

    monkeypatch.setattr(app_user_service, "get_organisation", mock_get_organisation)
    mocker.spy(app_user_service, "get_organisation")
