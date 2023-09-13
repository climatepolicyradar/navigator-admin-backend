"""
Please note:

Service mocks should only be used for router tests.
"""

from typing import Dict
from app.main import app
import pytest
from fastapi.testclient import TestClient

import app.service.family as family_service
import app.service.collection as collection_service
import app.service.token as token_service
from app.repository import (
    family_repo,
    geography_repo,
    metadata_repo,
    organisation_repo,
    collection_repo,
    app_user_repo,
)

from unit_tests.mocks.repos.app_user_repo import mock_app_user_repo
from unit_tests.mocks.repos.collection_repo import mock_collection_repo
from unit_tests.mocks.repos.family_repo import mock_family_repo
from unit_tests.mocks.repos.geography_repo import mock_geography_repo
from unit_tests.mocks.repos.metadata_repo import mock_metadata_repo
from unit_tests.mocks.repos.organisation_repo import mock_organisation_repo

from unit_tests.mocks.services.family_service import mock_family_service
from unit_tests.mocks.services.collection_service import mock_collection_service


@pytest.fixture
def client():
    """Get a TestClient instance that reads/write to the test database."""

    yield TestClient(app)


# ----- Mock repos


@pytest.fixture
def metadata_repo_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_metadata_repo(metadata_repo, monkeypatch, mocker)
    yield metadata_repo


@pytest.fixture
def app_user_repo_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_app_user_repo(app_user_repo, monkeypatch, mocker)
    yield app_user_repo


@pytest.fixture
def organisation_repo_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_organisation_repo(organisation_repo, monkeypatch, mocker)
    yield organisation_repo


@pytest.fixture
def geography_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_geography_repo(geography_repo, monkeypatch, mocker)
    yield geography_repo


@pytest.fixture
def family_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_family_repo(family_repo, monkeypatch, mocker)
    yield family_repo


@pytest.fixture
def collection_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_collection_repo(collection_repo, monkeypatch, mocker)
    yield collection_repo


# ----- Mock services


@pytest.fixture
def family_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_family_service(family_service, monkeypatch, mocker)
    yield family_service


@pytest.fixture
def collection_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_collection_service(collection_service, monkeypatch, mocker)
    yield collection_service


# ----- User tokens


@pytest.fixture
def superuser_header_token() -> Dict[str, str]:
    a_token = token_service.encode("test@cpr.org", True, {})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def user_header_token() -> Dict[str, str]:
    a_token = token_service.encode("test@cpr.org", False, {"is_admin": False})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def admin_user_header_token() -> Dict[str, str]:
    a_token = token_service.encode("test@cpr.org", False, {"is_admin": True})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers
