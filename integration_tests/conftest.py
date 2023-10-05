from typing import Dict
import uuid
from fastapi.testclient import TestClient
import pytest
from app.config import SQLALCHEMY_DATABASE_URI
from sqlalchemy_utils import create_database, database_exists, drop_database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.clients.db.session as db_session
from app.main import app
from integration_tests.mocks.bad_family_repo import mock_bad_family_repo, mock_family_count_none
from integration_tests.mocks.bad_collection_repo import mock_bad_collection_repo, mock_collection_count_none
from integration_tests.mocks.bad_document_repo import mock_bad_document_repo, mock_document_count_none
from integration_tests.mocks.rollback_collection_repo import (
    mock_rollback_collection_repo,
)
from integration_tests.mocks.rollback_document_repo import (
    mock_rollback_document_repo,
)
from integration_tests.mocks.rollback_family_repo import mock_rollback_family_repo
import app.service.token as token_service
from app.repository import family_repo, collection_repo, document_repo


def get_test_db_url() -> str:
    return SQLALCHEMY_DATABASE_URI + f"_test_{uuid.uuid4()}"


@pytest.fixture
def test_db(scope="function"):
    """Create a fresh test database for each test."""

    test_db_url = get_test_db_url()

    # Create the test database
    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)
    try:
        test_engine = create_engine(test_db_url)
        connection = test_engine.connect()
        db_session.Base.metadata.create_all(test_engine)  # type: ignore
        test_session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
        )
        test_session = test_session_maker()

        # Run the tests
        yield test_session
    finally:
        test_session.close()
        connection.close()
        # Drop the test database
        drop_database(test_db_url)


@pytest.fixture
def client(test_db, monkeypatch):
    """Get a TestClient instance that reads/write to the test database."""

    def get_test_db():
        return test_db

    monkeypatch.setattr(db_session, "get_db", get_test_db)

    yield TestClient(app)


@pytest.fixture
def bad_family_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_bad_family_repo(family_repo, monkeypatch, mocker)
    yield family_repo


@pytest.fixture
def bad_collection_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_bad_collection_repo(collection_repo, monkeypatch, mocker)
    yield collection_repo


@pytest.fixture
def bad_document_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_bad_document_repo(document_repo, monkeypatch, mocker)
    yield document_repo


@pytest.fixture
def bad_analytics_service(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_document_count_none(document_repo, monkeypatch, mocker)
    mock_family_count_none(family_repo, monkeypatch, mocker)
    mock_collection_count_none(collection_repo, monkeypatch, mocker)
    yield None


@pytest.fixture
def rollback_family_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_rollback_family_repo(family_repo, monkeypatch, mocker)
    yield family_repo


@pytest.fixture
def rollback_collection_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_rollback_collection_repo(collection_repo, monkeypatch, mocker)
    yield collection_repo


@pytest.fixture
def rollback_document_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_rollback_document_repo(document_repo, monkeypatch, mocker)
    yield document_repo


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
