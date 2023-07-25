import importlib
import sys
from app.main import app
import pytest
from fastapi.testclient import TestClient

import app.service.family as family_service
import app.repository.family as family_repo
from unit_tests.mocks.family_repo import mock_family_repo
from unit_tests.mocks.family_service import mock_family_service


@pytest.fixture
def client():
    """Get a TestClient instance that reads/write to the test database."""

    yield TestClient(app)


@pytest.fixture()
def clean_family_repo():
    """
    Resets the repo while we have an in-memory one.

    This is only temporary until we get a real db fixture
    """
    module = "app.repository.family"
    mod = importlib.import_module(module)
    yield mod
    del sys.modules[module]


@pytest.fixture
def family_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_family_service(family_service, monkeypatch, mocker)
    yield family_service


@pytest.fixture
def family_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_family_repo(family_repo, monkeypatch, mocker)
    yield family_repo
