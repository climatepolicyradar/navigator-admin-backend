from typing import Optional

from pytest import MonkeyPatch

ALTERNATIVE_ORG_ID = 999
STANDARD_ORG_ID = 1


def mock_app_user_service(app_user_service, monkeypatch: MonkeyPatch, mocker):
    app_user_service.alternative_org = False
    app_user_service.superuser = False

    def mock_get_organisation(_, user_email: str) -> int:
        if app_user_service.alternative_org:
            return ALTERNATIVE_ORG_ID
        return STANDARD_ORG_ID

    def mock_restrict_entities_to_user_org(user_email: str) -> Optional[int]:
        if app_user_service.superuser is True:
            return None
        if app_user_service.alternative_org:
            return ALTERNATIVE_ORG_ID
        return STANDARD_ORG_ID

    monkeypatch.setattr(
        app_user_service,
        "restrict_entities_to_user_org",
        mock_restrict_entities_to_user_org,
    )
    mocker.spy(app_user_service, "restrict_entities_to_user_org")

    monkeypatch.setattr(app_user_service, "get_organisation", mock_get_organisation)
    mocker.spy(app_user_service, "get_organisation")
