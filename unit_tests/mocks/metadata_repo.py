from typing import Optional
from pytest import MonkeyPatch

from app.model.general import Json


def mock_metadata_repo(metadata_repo, monkeypatch: MonkeyPatch, mocker):
    def mock_get_schema_for_org(_, __) -> Optional[Json]:
        if not metadata_repo.error:
            return {}

    metadata_repo.error = False
    monkeypatch.setattr(metadata_repo, "get_schema_for_org", mock_get_schema_for_org)
    mocker.spy(metadata_repo, "get_schema_for_org")
