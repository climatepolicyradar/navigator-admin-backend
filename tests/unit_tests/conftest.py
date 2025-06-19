"""
Please note:

Service mocks should only be used for router tests.
"""

import os
from typing import Dict
from unittest.mock import MagicMock, patch

import boto3
import db_client.functions.corpus_helpers as db_client_corpus_helpers
import db_client.functions.metadata as db_client_metadata
import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from moto import mock_aws

import app.service.analytics as analytics_service
import app.service.app_user as app_user_service
import app.service.bulk_import as bulk_import_service
import app.service.collection as collection_service
import app.service.config as config_service
import app.service.corpus as corpus_service
import app.service.corpus_type as corpus_type_service
import app.service.document as document_service
import app.service.event as event_service
import app.service.family as family_service
import app.service.taxonomy as taxonomy_service
import app.service.token as token_service
import app.service.validation as validation_service
from app.clients.aws.client import get_s3_client
from app.main import app
from app.model.user import UserContext
from app.repository import (
    app_user_repo,
    collection_repo,
    config_repo,
    corpus_repo,
    corpus_type_repo,
    document_repo,
    event_repo,
    family_repo,
    geography_repo,
    organisation_repo,
)
from tests.mocks.repos import create_mock_family_repo
from tests.mocks.repos.app_user_repo import mock_app_user_repo
from tests.mocks.repos.collection_repo import mock_collection_repo
from tests.mocks.repos.config_repo import mock_config_repo
from tests.mocks.repos.corpus_repo import mock_corpus_repo
from tests.mocks.repos.corpus_type_repo import mock_corpus_type_repo
from tests.mocks.repos.db_client_corpus_helpers import mock_corpus_helpers_db_client
from tests.mocks.repos.db_client_metadata import mock_metadata_db_client
from tests.mocks.repos.document_repo import mock_document_repo
from tests.mocks.repos.event_repo import mock_event_repo
from tests.mocks.repos.geography_repo import mock_geography_repo
from tests.mocks.repos.organisation_repo import mock_organisation_repo
from tests.mocks.services.analytics_service import mock_analytics_service
from tests.mocks.services.app_user_service import mock_app_user_service
from tests.mocks.services.bulk_import_service import mock_bulk_import_service
from tests.mocks.services.collection_service import mock_collection_service
from tests.mocks.services.config_service import mock_config_service
from tests.mocks.services.corpus_service import mock_corpus_service
from tests.mocks.services.corpus_type_service import mock_corpus_type_service
from tests.mocks.services.document_service import mock_document_service
from tests.mocks.services.event_service import mock_event_service
from tests.mocks.services.family_service import mock_family_service
from tests.mocks.services.validation_service import mock_validation_service

ORG_ID = 1


@pytest.fixture
def client():
    """Get a TestClient instance that reads/write to the test database."""

    yield TestClient(app)


@pytest.fixture
def db_session_mock():
    return MagicMock()


# ----- Mock repos


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

    # set some attributes for testing purposes...
    family_repo.return_empty = False
    family_repo.throw_repository_error = False
    family_repo.throw_timeout_error = False
    family_repo.no_org = False
    family_repo.alternative_org = False

    create_mock_family_repo(family_repo, monkeypatch, mocker)
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


@pytest.fixture
def corpus_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_corpus_repo(corpus_repo, monkeypatch, mocker)
    yield corpus_repo


@pytest.fixture
def corpus_type_repo_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_corpus_type_repo(corpus_type_repo, monkeypatch, mocker)
    yield corpus_type_repo


@pytest.fixture
def db_client_metadata_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_metadata_db_client(db_client_metadata, monkeypatch, mocker)
    yield db_client_metadata


@pytest.fixture
def db_client_corpus_helpers_mock(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_corpus_helpers_db_client(taxonomy_service, monkeypatch, mocker)
    yield db_client_corpus_helpers


# ----- Mock services


@pytest.fixture
def app_user_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_app_user_service(app_user_service, monkeypatch, mocker)
    yield app_user_service


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


@pytest.fixture
def corpus_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_corpus_service(corpus_service, monkeypatch, mocker)
    yield corpus_service


@pytest.fixture
def corpus_type_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_corpus_type_service(corpus_type_service, monkeypatch, mocker)
    yield corpus_type_service


@pytest.fixture
def bulk_import_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_bulk_import_service(bulk_import_service, monkeypatch, mocker)
    yield bulk_import_service


@pytest.fixture
def validation_service_mock(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_validation_service(validation_service, monkeypatch, mocker)
    yield validation_service


# ----- User tokens


@pytest.fixture
def superuser_header_token() -> Dict[str, str]:
    a_token = token_service.encode("super@cpr.org", ORG_ID, True, {"is_admin": True})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def non_admin_superuser_header_token() -> Dict[str, str]:
    a_token = token_service.encode("non-admin-super@cpr.org", ORG_ID, True, {})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def user_header_token() -> Dict[str, str]:
    a_token = token_service.encode("cclw@cpr.org", ORG_ID, False, {"is_admin": False})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def admin_user_header_token() -> Dict[str, str]:
    a_token = token_service.encode("admin@cpr.org", ORG_ID, False, {"is_admin": True})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def non_cclw_user_header_token() -> Dict[str, str]:
    a_token = token_service.encode("unfccc@cpr.org", ORG_ID, False, {"is_admin": False})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def invalid_user_header_token() -> Dict[str, str]:
    a_token = token_service.encode("non-admin@cpr.org", ORG_ID, False, {})
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
    region = "eu-west-1"

    with patch.dict(
        os.environ,
        {
            "AWS_ENDPOINT_URL": "",
            "AWS_ACCESS_KEY_ID": "test",
            "AWS_SECRET_ACCESS_KEY": "test",
        },
        clear=True,
    ):
        with mock_aws():
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


@pytest.fixture
def basic_s3_client():
    bucket_name = "test_bucket"
    with mock_aws():
        with patch.dict(
            os.environ,
            {
                "AWS_ACCESS_KEY_ID": "test",
                "AWS_SECRET_ACCESS_KEY": "test",
                "AWS_ENDPOINT_URL": "",
            },
            clear=True,
        ):
            conn = boto3.client("s3")
            try:
                conn.head_bucket(Bucket=bucket_name)
            except ClientError:
                conn.create_bucket(Bucket=bucket_name)
            yield conn


# -- now UserContexts
@pytest.fixture
def super_user_context():
    return UserContext(
        email="super@here.com", org_id=50, is_superuser=True, authorisation={}
    )


@pytest.fixture
def admin_user_context():
    return UserContext(
        email="admin@here.com", org_id=1, is_superuser=False, authorisation={}
    )


@pytest.fixture
def another_admin_user_context():
    return UserContext(
        email="another-admin@here.com", org_id=3, is_superuser=False, authorisation={}
    )


@pytest.fixture
def bad_user_context():
    return UserContext(
        email="not-an-email", org_id=0, is_superuser=False, authorisation={}
    )
