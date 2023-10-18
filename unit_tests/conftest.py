"""
Please note:

Service mocks should only be used for router tests.
"""

from typing import Dict
from app.clients.aws.client import get_s3_client
from app.main import app
import pytest
from fastapi.testclient import TestClient
from moto import mock_s3

import app.service.family as family_service
import app.service.collection as collection_service
import app.service.document as document_service
import app.service.config as config_service
import app.service.token as token_service
import app.service.analytics as analytics_service
import app.service.event as event_service
from app.repository import (
    family_repo,
    geography_repo,
    metadata_repo,
    organisation_repo,
    collection_repo,
    app_user_repo,
    config_repo,
    document_repo,
    event_repo,
)

from unit_tests.mocks.repos.app_user_repo import mock_app_user_repo
from unit_tests.mocks.repos.collection_repo import mock_collection_repo
from unit_tests.mocks.repos.document_repo import mock_document_repo
from unit_tests.mocks.repos.family_repo import mock_family_repo

from unit_tests.mocks.repos.geography_repo import mock_geography_repo
from unit_tests.mocks.repos.metadata_repo import mock_metadata_repo
from unit_tests.mocks.repos.organisation_repo import mock_organisation_repo
from unit_tests.mocks.repos.config_repo import mock_config_repo
from unit_tests.mocks.repos.event_repo import mock_event_repo

from unit_tests.mocks.services.family_service import mock_family_service
from unit_tests.mocks.services.collection_service import mock_collection_service
from unit_tests.mocks.services.document_service import mock_document_service
from unit_tests.mocks.services.config_service import mock_config_service
from unit_tests.mocks.services.analytics_service import mock_analytics_service
from unit_tests.mocks.services.event_service import mock_event_service


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


@pytest.fixture
def document_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_document_repo(document_repo, monkeypatch, mocker)
    yield document_repo


@pytest.fixture
def config_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_config_repo(config_repo, monkeypatch, mocker)
    yield config_repo


@pytest.fixture
def event_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_event_repo(event_repo, monkeypatch, mocker)
    yield event_repo


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


@pytest.fixture
def document_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_document_service(document_service, monkeypatch, mocker)
    yield document_service


@pytest.fixture
def config_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_config_service(config_service, monkeypatch, mocker)
    yield config_service


@pytest.fixture
def analytics_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_analytics_service(analytics_service, monkeypatch, mocker)
    yield analytics_service


@pytest.fixture
def event_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_event_service(event_service, monkeypatch, mocker)
    yield event_service


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


@pytest.fixture
def s3_document_bucket_names() -> dict:
    return {
        "queue": "cpr-document-queue",
    }


@pytest.fixture
def test_s3_client(s3_document_bucket_names):
    bucket_names = s3_document_bucket_names.values()
    region = "eu-west-2"

    with mock_s3():
        s3_client = get_s3_client()
        for bucket in bucket_names:
            s3_client.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={"LocationConstraint": region},
            )

        # Test document in queue for action submission
        s3_client.put_object(
            Bucket=s3_document_bucket_names["queue"],
            Key="test_document.pdf",
            Body=bytes(1024),
        )

        yield s3_client
