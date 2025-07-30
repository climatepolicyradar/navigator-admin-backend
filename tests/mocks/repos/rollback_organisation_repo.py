from pytest import MonkeyPatch

from app.model.organisation import OrganisationCreateDTO, OrganisationWriteDTO


def mock_rollback_organisation_repo(
    organisation_repo, monkeypatch: MonkeyPatch, mocker
):
    actual_create = organisation_repo.create
    actual_update = organisation_repo.update

    def mock_create_organisation(db, data: OrganisationCreateDTO) -> int:
        actual_create(db, data)
        raise Exception("Error creating an organisation")

    def mock_update_organisation(db, id: int, data: OrganisationWriteDTO) -> int:
        actual_update(db, id, data)
        raise Exception(f"Error updating organisation: {id}")

    monkeypatch.setattr(organisation_repo, "create", mock_create_organisation)
    mocker.spy(organisation_repo, "create")

    monkeypatch.setattr(organisation_repo, "update", mock_update_organisation)
    mocker.spy(organisation_repo, "update")
