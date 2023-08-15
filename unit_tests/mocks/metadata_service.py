from pytest import MonkeyPatch

from app.errors.validation_error import ValidationError
from app.model.general import Json


def mock_validate(_, org_id: int, data: Json) -> int:
    if data == {"invalid": True}:
        raise ValidationError("Invalid Metadata")
    return 1


def mock_metadata_service(metadata_service, monkeypatch: MonkeyPatch, mocker):
    monkeypatch.setattr(metadata_service, "validate", mock_validate)
    mocker.spy(metadata_service, "validate")
