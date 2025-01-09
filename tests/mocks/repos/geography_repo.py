from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError


def mock_geography_repo(geography_repo, monkeypatch: MonkeyPatch, mocker):
    geography_repo.return_empty = False
    geography_repo.failed_to_remove_geography = False
    geography_repo.failed_to_add_geography = False

    def maybe_throw():
        if geography_repo.failed_to_remove_geography:
            raise RepositoryError("Failed to remove geography from family")
        if geography_repo.failed_to_add_geography:
            raise RepositoryError("Failed to add geography to family")

    def mock_get_id_from_value(_, __) -> Optional[int]:
        maybe_throw()
        if not geography_repo.error:
            return 1
        return None

    def mock_get_ids_from_values(_, __) -> list[int]:
        maybe_throw()
        if not geography_repo.error:
            return [1, 2]
        return []

    geography_repo.error = False
    monkeypatch.setattr(geography_repo, "get_ids_from_values", mock_get_ids_from_values)
    monkeypatch.setattr(geography_repo, "get_id_from_value", mock_get_id_from_value)
    mocker.spy(geography_repo, "get_id_from_value")
    mocker.spy(geography_repo, "get_ids_from_values")
