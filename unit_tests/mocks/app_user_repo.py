from typing import Tuple
from pytest import MonkeyPatch
from app.db.models.app.users import AppUser, Organisation, OrganisationUser

from app.repository.app_user import MaybeAppUser
import app.service.authentication as auth_service


PLAIN_PASSWORD = "test-password"
HASH_PASSWORD = auth_service.get_password_hash(PLAIN_PASSWORD)


def mock_app_user_repo(app_user_repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_app_user_authorisation(
        _, __
    ) -> list[Tuple[OrganisationUser, Organisation]]:
        return []

    def mock_get_user_by_email(_, __) -> MaybeAppUser:
        if not app_user_repo.error:
            return AppUser(
                email="bob@here.com",
                name="Bob",
                hashed_password=HASH_PASSWORD,
                is_superuser=True,
            )

    app_user_repo.error = False
    monkeypatch.setattr(app_user_repo, "get_user_by_email", mock_get_user_by_email)
    monkeypatch.setattr(
        app_user_repo, "get_app_user_authorisation", mock_get_app_user_authorisation
    )
    mocker.spy(app_user_repo, "get_user_by_email")
