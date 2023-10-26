from typing import Tuple
from pytest import MonkeyPatch
from app.clients.db.models.app.users import AppUser, Organisation, OrganisationUser

from app.repository.app_user import MaybeAppUser
import app.service.authentication as auth_service


PLAIN_PASSWORD = "test-password"
HASH_PASSWORD = auth_service.get_password_hash(PLAIN_PASSWORD)
VALID_USERNAME = "bob@here.com"

ORG_ID = 1234


def mock_app_user_repo(app_user_repo, monkeypatch: MonkeyPatch, mocker):
    app_user_repo.user_active = True
    app_user_repo.error = False
    app_user_repo.invalid_org = False

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
            return ORG_ID
        return 1

    def mock_is_active(_, email: str) -> bool:
        return app_user_repo.user_active

    monkeypatch.setattr(app_user_repo, "get_user_by_email", mock_get_user_by_email)
    monkeypatch.setattr(app_user_repo, "get_org_id", mock_get_org_id)
    monkeypatch.setattr(app_user_repo, "is_active", mock_is_active)
    monkeypatch.setattr(
        app_user_repo, "get_app_user_authorisation", mock_get_app_user_authorisation
    )
    mocker.spy(app_user_repo, "get_user_by_email")
    mocker.spy(app_user_repo, "get_org_id")
    mocker.spy(app_user_repo, "is_active")
    mocker.spy(app_user_repo, "get_app_user_authorisation")
