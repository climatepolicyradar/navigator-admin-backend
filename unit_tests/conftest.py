from app.main import app
import pytest
from fastapi.testclient import TestClient

import app.service.family as family_service
import app.repository.family as family_repo
import app.repository.geography as geography_repo
import app.repository.metadata as metadata_repo
import app.repository.organisation as organisation_repo
from unit_tests.mocks.family_repo import mock_family_repo
from unit_tests.mocks.family_service import mock_family_service
from unit_tests.mocks.geography_repo import mock_geography_repo
from unit_tests.mocks.metadata_repo import mock_metadata_repo
from unit_tests.mocks.organisation_repo import mock_organisation_repo


@pytest.fixture
def client():
    """Get a TestClient instance that reads/write to the test database."""

    yield TestClient(app)


@pytest.fixture
def metadata_repo_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_metadata_repo(metadata_repo, monkeypatch, mocker)
    yield metadata_repo


@pytest.fixture
def organisation_repo_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_organisation_repo(organisation_repo, monkeypatch, mocker)
    yield organisation_repo


@pytest.fixture
def family_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_family_service(family_service, monkeypatch, mocker)
    yield family_service


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
