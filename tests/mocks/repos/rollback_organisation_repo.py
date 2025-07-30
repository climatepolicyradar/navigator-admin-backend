from pytest import MonkeyPatch

from app.model.organisation import OrganisationCreateDTO


def mock_rollback_organisation_repo(
    organisation_repo, monkeypatch: MonkeyPatch, mocker
):
    actual_create = organisation_repo.create

    def mock_create_organisation(db, data: OrganisationCreateDTO) -> int:
        actual_create(db, data)
        raise Exception("Error creating an organisation")

    monkeypatch.setattr(organisation_repo, "create", mock_create_organisation)
    mocker.spy(organisation_repo, "create")
