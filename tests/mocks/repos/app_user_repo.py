from typing import Tuple

from db_client.models.organisation.users import AppUser, Organisation, OrganisationUser
from pytest import MonkeyPatch

import app.service.authentication as auth_service
from app.repository.app_user import MaybeAppUser

PLAIN_PASSWORD = "test-password"
HASH_PASSWORD = auth_service.get_password_hash(PLAIN_PASSWORD)
VALID_USERNAME = "bob@here.com"

INVALID_ORG_ID = 1234


def mock_app_user_repo(app_user_repo, monkeypatch: MonkeyPatch, mocker):
    app_user_repo.user_active = True
    app_user_repo.error = False
    app_user_repo.invalid_org = False
    app_user_repo.superuser = False

    def mock_get_app_user_authorisation(
        _, __
    ) -> list[Tuple[OrganisationUser, Organisation]]:
        return []

    def mock_get_user_by_email(_, __) -> MaybeAppUser:
        if not app_user_repo.error:
            return AppUser(
                email=VALID_USERNAME,
                name="Bob",
                hashed_password=HASH_PASSWORD,
                is_superuser=True,
            )

    def mock_get_org_id(_, user_email: str) -> int:
        if app_user_repo.invalid_org is True:
            return INVALID_ORG_ID
        return 1

    def mock_is_active(_, email: str) -> bool:
        return bool(app_user_repo.user_active is True)

    def mock_is_superuser(_, email: str) -> bool:
        print(bool(app_user_repo.superuser is True))
        return bool(app_user_repo.superuser is True)

    monkeypatch.setattr(app_user_repo, "get_user_by_email", mock_get_user_by_email)
    mocker.spy(app_user_repo, "get_user_by_email")

    monkeypatch.setattr(app_user_repo, "get_org_id", mock_get_org_id)
    mocker.spy(app_user_repo, "get_org_id")

    monkeypatch.setattr(app_user_repo, "is_active", mock_is_active)
    mocker.spy(app_user_repo, "is_active")

    monkeypatch.setattr(
        app_user_repo, "get_app_user_authorisation", mock_get_app_user_authorisation
    )
    mocker.spy(app_user_repo, "get_app_user_authorisation")

    monkeypatch.setattr(app_user_repo, "is_superuser", mock_is_superuser)
    mocker.spy(app_user_repo, "is_superuser")
