from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError
from app.model.organisation import OrganisationCreateDTO


def mock_organisation_repo(organisation_repo, monkeypatch: MonkeyPatch, mocker):
    organisation_repo.throw_repository_error = False
    organisation_repo.error = False

    def maybe_throw():
        if organisation_repo.throw_repository_error:
            raise RepositoryError("Repository Error: Bad organisation repo")

    def mock_get_id_from_name(_, __) -> Optional[int]:
        if not organisation_repo.error:
            return 1

    def mock_create(_, data: OrganisationCreateDTO) -> int:
        maybe_throw()
        if organisation_repo.throw_repository_error:
            raise RepositoryError("Error trying to create Event")
        return 1

    monkeypatch.setattr(organisation_repo, "get_id_from_name", mock_get_id_from_name)
    mocker.spy(organisation_repo, "get_id_from_name")

    monkeypatch.setattr(organisation_repo, "create", mock_create)
    mocker.spy(organisation_repo, "create")
