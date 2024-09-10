from pytest import MonkeyPatch

from app.errors import ValidationError


def mock_validation_service(validation_service, monkeypatch: MonkeyPatch, mocker):
    validation_service.org_mismatch = False
    validation_service.throw_validation_error = False

    def maybe_throw():
        if validation_service.throw_validation_error:
            raise ValidationError("Error")

    def mock_validate_collection(_) -> None:
        maybe_throw()

    def mock_validate_family(_, __) -> None:
        maybe_throw()

    def mock_validate_families(_, __) -> None:
        maybe_throw()

    def mock_validate_document(_, __) -> None:
        maybe_throw()

    def mock_validate_event(_, __) -> None:
        maybe_throw()

    def mock_validate_events(_, __) -> None:
        maybe_throw()

    monkeypatch.setattr(
        validation_service, "validate_collection", mock_validate_collection
    )
    mocker.spy(validation_service, "validate_collection")

    monkeypatch.setattr(validation_service, "validate_family", mock_validate_family)
    mocker.spy(validation_service, "validate_family")

    monkeypatch.setattr(validation_service, "validate_families", mock_validate_families)
    mocker.spy(validation_service, "validate_families")

    monkeypatch.setattr(validation_service, "validate_document", mock_validate_document)
    mocker.spy(validation_service, "validate_document")

    monkeypatch.setattr(validation_service, "validate_event", mock_validate_event)
    mocker.spy(validation_service, "validate_event")

    monkeypatch.setattr(validation_service, "validate_events", mock_validate_events)
    mocker.spy(validation_service, "validate_events")
