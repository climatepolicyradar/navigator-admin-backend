"""Unit tests for organisation service orchestration."""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import app.service.organisation as organisation_service
from app.model.organisation import (
    OrganisationCreateDTO,
    OrganisationReadDTO,
    OrganisationWriteDTO,
)


@pytest.fixture
def org_service_mocks(monkeypatch) -> SimpleNamespace:
    """Patch DB session and organisation repository for service tests.

    :param monkeypatch: Pytest monkeypatch fixture.
    :return: Namespace with session and repository mocks.
    :rtype: SimpleNamespace
    """
    session = MagicMock()

    @contextmanager
    def fake_get_db():
        yield session

    monkeypatch.setattr(organisation_service.db_session, "get_db", fake_get_db)

    create_mock = MagicMock(return_value=42)
    ensure_mock = MagicMock()
    update_mock = MagicMock(return_value=True)
    get_by_id_mock = MagicMock()

    monkeypatch.setattr(organisation_service.organisation_repo, "create", create_mock)
    monkeypatch.setattr(
        organisation_service.organisation_repo,
        "ensure_entity_counter_for_organisation",
        ensure_mock,
    )
    monkeypatch.setattr(organisation_service.organisation_repo, "update", update_mock)
    monkeypatch.setattr(
        organisation_service.organisation_repo, "get_by_id", get_by_id_mock
    )

    return SimpleNamespace(
        session=session,
        create=create_mock,
        ensure=ensure_mock,
        update=update_mock,
        get_by_id=get_by_id_mock,
    )


def _sample_create_dto() -> OrganisationCreateDTO:
    return OrganisationCreateDTO(
        internal_name="Acme Ltd",
        display_name="Acme",
        description="Widgets",
        type="ORG",
        attribution_url=None,
    )


def _sample_write_dto() -> OrganisationWriteDTO:
    return OrganisationWriteDTO(
        internal_name="Acme Ltd",
        display_name="Acme",
        description="Widgets",
        type="ORG",
        attribution_url=None,
    )


def test_create_calls_ensure_entity_counter_with_session_and_name(org_service_mocks):
    dto = _sample_create_dto()
    assert organisation_service.create(dto) == 42
    org_service_mocks.create.assert_called_once_with(org_service_mocks.session, dto)
    org_service_mocks.ensure.assert_called_once_with(
        org_service_mocks.session, "Acme Ltd"
    )
    org_service_mocks.session.commit.assert_called()


def test_create_does_not_call_ensure_when_create_raises(monkeypatch):
    session = MagicMock()

    @contextmanager
    def fake_get_db():
        yield session

    monkeypatch.setattr(organisation_service.db_session, "get_db", fake_get_db)
    monkeypatch.setattr(
        organisation_service.organisation_repo,
        "create",
        MagicMock(side_effect=RuntimeError("persist failed")),
    )
    ensure_mock = MagicMock()
    monkeypatch.setattr(
        organisation_service.organisation_repo,
        "ensure_entity_counter_for_organisation",
        ensure_mock,
    )

    with pytest.raises(RuntimeError, match="persist failed"):
        organisation_service.create(_sample_create_dto())

    ensure_mock.assert_not_called()


def test_update_calls_ensure_when_row_changed(org_service_mocks):
    org_service_mocks.update.return_value = True
    org_service_mocks.get_by_id.return_value = OrganisationReadDTO(
        id=7,
        internal_name="Acme Ltd",
        display_name="Acme",
        description="Widgets",
        type="ORG",
        attribution_url=None,
    )
    dto = _sample_write_dto()

    result = organisation_service.update(7, dto)

    assert result is not None
    org_service_mocks.update.assert_called_once_with(org_service_mocks.session, 7, dto)
    org_service_mocks.ensure.assert_called_once_with(
        org_service_mocks.session, "Acme Ltd"
    )
    org_service_mocks.session.commit.assert_called()


def test_update_calls_ensure_when_row_unchanged(org_service_mocks):
    """No-op UPDATE still backfills a missing entity_counter."""
    org_service_mocks.update.return_value = False
    org_service_mocks.get_by_id.return_value = OrganisationReadDTO(
        id=7,
        internal_name="Acme Ltd",
        display_name="Acme",
        description="Widgets",
        type="ORG",
        attribution_url=None,
    )
    dto = _sample_write_dto()

    organisation_service.update(7, dto)

    org_service_mocks.ensure.assert_called_once_with(
        org_service_mocks.session, "Acme Ltd"
    )
    org_service_mocks.session.commit.assert_called()


def test_update_skips_ensure_when_organisation_missing(org_service_mocks):
    org_service_mocks.update.return_value = None
    org_service_mocks.get_by_id.return_value = None
    dto = _sample_write_dto()

    result = organisation_service.update(999, dto)

    assert result is None
    org_service_mocks.ensure.assert_not_called()
    org_service_mocks.session.rollback.assert_called()
    org_service_mocks.session.commit.assert_not_called()
