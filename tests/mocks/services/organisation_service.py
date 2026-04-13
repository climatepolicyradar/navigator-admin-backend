"""Test doubles for :mod:`app.service.organisation`."""

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

from pytest import MonkeyPatch


def mock_organisation_service(
    organisation_service: Any,
    monkeypatch: MonkeyPatch,
    _mocker: Any,
) -> SimpleNamespace:
    """Patch DB context, repository methods, and service ``get``.

    Replaces ``get`` so ``@validate_call`` does not reject a
    ``MagicMock`` session.

    :param organisation_service: Loaded ``app.service.organisation``
        module.
    :type organisation_service: Any
    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: MonkeyPatch
    :param _mocker: Pytest-mock plugin (unused; API parity with other
        service mocks).
    :type _mocker: Any
    :return: Session and repository ``MagicMock`` handles.
    :rtype: SimpleNamespace
    """
    session = MagicMock()
    repo = organisation_service.organisation_repo

    @contextmanager
    def mock_get_db():
        yield session

    create_mock = MagicMock(return_value=42)
    ensure_mock = MagicMock()
    update_mock = MagicMock(return_value=True)
    get_by_id_mock = MagicMock()

    def mock_get(organisation: int, db=None):
        return get_by_id_mock(db, organisation)

    monkeypatch.setattr(organisation_service.db_session, "get_db", mock_get_db)
    monkeypatch.setattr(repo, "create", create_mock)
    monkeypatch.setattr(
        repo,
        "ensure_entity_counter_for_organisation",
        ensure_mock,
    )
    monkeypatch.setattr(repo, "update", update_mock)
    monkeypatch.setattr(repo, "get_by_id", get_by_id_mock)
    monkeypatch.setattr(organisation_service, "get", mock_get)

    return SimpleNamespace(
        session=session,
        create=create_mock,
        ensure=ensure_mock,
        update=update_mock,
        get_by_id=get_by_id_mock,
    )
