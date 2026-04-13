"""Unit tests for organisation service orchestration."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

import app.service.organisation as organisation_service
from tests.helpers.organisation import (
    create_organisation_create_dto,
    create_organisation_read_dto,
    create_organisation_write_dto,
)


def test_create_calls_ensure_entity_counter_with_session_and_name(
    organisation_service_mock,
):
    dto = create_organisation_create_dto()
    assert organisation_service.create(dto) == 42
    organisation_service_mock.create.assert_called_once_with(
        organisation_service_mock.session,
        dto,
    )
    organisation_service_mock.ensure.assert_called_once_with(
        organisation_service_mock.session,
        "Acme Ltd",
    )
    organisation_service_mock.session.commit.assert_called()


def test_create_does_not_call_ensure_when_create_raises(
    monkeypatch,
    organisation_service_mock,
):
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
        organisation_service.create(create_organisation_create_dto())

    ensure_mock.assert_not_called()


def test_update_calls_ensure_when_row_changed(organisation_service_mock):
    organisation_service_mock.update.return_value = True
    organisation_service_mock.get_by_id.return_value = create_organisation_read_dto(
        id=7
    )
    dto = create_organisation_write_dto()

    result = organisation_service.update(7, dto)

    assert result is not None
    organisation_service_mock.update.assert_called_once_with(
        organisation_service_mock.session,
        7,
        dto,
    )
    organisation_service_mock.ensure.assert_called_once_with(
        organisation_service_mock.session,
        "Acme Ltd",
    )
    organisation_service_mock.session.commit.assert_called()


def test_update_calls_ensure_when_row_unchanged(organisation_service_mock):
    """No-op UPDATE still backfills a missing entity_counter."""
    organisation_service_mock.update.return_value = False
    organisation_service_mock.get_by_id.return_value = create_organisation_read_dto(
        id=7
    )
    dto = create_organisation_write_dto()

    organisation_service.update(7, dto)

    organisation_service_mock.ensure.assert_called_once_with(
        organisation_service_mock.session,
        "Acme Ltd",
    )
    organisation_service_mock.session.commit.assert_called()


def test_update_skips_ensure_when_organisation_missing(
    organisation_service_mock,
):
    organisation_service_mock.update.return_value = None
    organisation_service_mock.get_by_id.return_value = None
    dto = create_organisation_write_dto()

    result = organisation_service.update(999, dto)

    assert result is None
    organisation_service_mock.ensure.assert_not_called()
    organisation_service_mock.session.rollback.assert_called()
    organisation_service_mock.session.commit.assert_not_called()
