import os
import uuid
from typing import Dict, Generator

import boto3
import pytest
from botocore.exceptions import ClientError
from db_client import run_migrations
from fastapi.testclient import TestClient
from moto import mock_s3
from sqlalchemy import create_engine
from sqlalchemy.engine import Connection
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

import app.clients.db.session as db_session
import app.service.token as token_service
from app.config import SQLALCHEMY_DATABASE_URI
from app.main import app
from app.repository import collection_repo, document_repo, event_repo, family_repo
from tests.mocks.repos.bad_collection_repo import (
    mock_bad_collection_repo,
    mock_collection_count_none,
)
from tests.mocks.repos.bad_document_repo import (
    mock_bad_document_repo,
    mock_document_count_none,
)
from tests.mocks.repos.bad_event_repo import mock_bad_event_repo, mock_event_count_none
from tests.mocks.repos.bad_family_repo import (
    mock_bad_family_repo,
    mock_family_count_none,
)
from tests.mocks.repos.rollback_collection_repo import mock_rollback_collection_repo
from tests.mocks.repos.rollback_document_repo import mock_rollback_document_repo
from tests.mocks.repos.rollback_event_repo import mock_rollback_event_repo
from tests.mocks.repos.rollback_family_repo import mock_rollback_family_repo

CCLW_ORG_ID = 1
UNFCCC_ORG_ID = 2
SUPER_ORG_ID = 50


def get_test_db_url() -> str:
    return SQLALCHEMY_DATABASE_URI + f"_test_{uuid.uuid4()}"


@pytest.fixture(scope="function")
def slow_db(monkeypatch):
    """Create a fresh test database for each test."""

    test_db_url = get_test_db_url()

    # Create the test database
    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)

    test_session = None
    connection = None
    try:
        test_engine = create_engine(test_db_url)
        connection = test_engine.connect()

        run_migrations(test_engine)
        test_session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
        )
        test_session = test_session_maker()

        def get_test_db():
            return test_session

        monkeypatch.setattr(db_session, "get_db", get_test_db)
        # Run the tests
        yield test_session
    finally:
        if test_session is not None:
            test_session.close()

        if connection is not None:
            connection.close()
        # Drop the test database
        drop_database(test_db_url)


@pytest.fixture(scope="session")
def data_db_connection() -> Generator[Connection, None, None]:
    test_db_url = get_test_db_url()

    if database_exists(test_db_url):
        drop_database(test_db_url)
    create_database(test_db_url)

    saved_db_url = os.environ["DATABASE_URL"]
    os.environ["DATABASE_URL"] = test_db_url

    test_engine = create_engine(test_db_url)

    run_migrations(test_engine)
    connection = test_engine.connect()

    yield connection
    connection.close()

    os.environ["DATABASE_URL"] = saved_db_url
    drop_database(test_db_url)


@pytest.fixture(scope="function")
def data_db(slow_db):
    yield slow_db


# @pytest.fixture(scope="function")
# def data_db(data_db_connection, monkeypatch):

#     outer = data_db_connection.begin_nested()
#     SessionLocal = sessionmaker(
#         autocommit=False, autoflush=False, bind=data_db_connection
#     )
#     session = SessionLocal()

#     def get_test_db():
#         return session

#     monkeypatch.setattr(db_session, "get_db", get_test_db)
#     yield session
#     if not outer.is_active:
#         print("Outer transaction already completed.")
#         #raise RuntimeError("Outer transaction already completed.")
#     else:
#         outer.rollback()
#     n_cols = data_db_connection.execute("select count(*) from collection")
#     if n_cols.scalar() != 0:
#         raise RuntimeError("Database not cleaned up properly")


@pytest.fixture
def client():
    """Get a TestClient instance that reads/write to the test database."""

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
def bad_event_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_bad_event_repo(event_repo, monkeypatch, mocker)
    yield event_repo


@pytest.fixture
def collection_count_none(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_collection_count_none(collection_repo, monkeypatch, mocker)
    yield collection_repo


@pytest.fixture
def family_repo_count_none(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_family_count_none(family_repo, monkeypatch, mocker)
    yield family_repo


@pytest.fixture
def document_count_none(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_document_count_none(document_repo, monkeypatch, mocker)
    yield document_repo


@pytest.fixture
def event_count_none(monkeypatch, mocker):
    """Mocks the service for a single test."""
    mock_event_count_none(event_repo, monkeypatch, mocker)
    yield event_repo


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
def rollback_event_repo(monkeypatch, mocker):
    """Mocks the repository for a single test."""
    mock_rollback_event_repo(event_repo, monkeypatch, mocker)
    yield event_repo


@pytest.fixture
def superuser_header_token() -> Dict[str, str]:
    a_token = token_service.encode(
        "super@cpr.org", SUPER_ORG_ID, True, {"is_admin": True}
    )
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def non_admin_superuser_header_token() -> Dict[str, str]:
    a_token = token_service.encode("non-admin-super@cpr.org", SUPER_ORG_ID, True, {})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def user_header_token() -> Dict[str, str]:
    a_token = token_service.encode(
        "cclw@cpr.org", CCLW_ORG_ID, False, {"is_admin": True}
    )
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def non_cclw_user_header_token() -> Dict[str, str]:
    a_token = token_service.encode(
        "unfccc@cpr.org", UNFCCC_ORG_ID, False, {"is_admin": True}
    )
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def non_admin_user_header_token() -> Dict[str, str]:
    a_token = token_service.encode("non-admin@cpr.org", CCLW_ORG_ID, False, {})
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers


@pytest.fixture
def basic_s3_client():
    bucket_name = os.environ["INGEST_JSON_BUCKET"]
    with mock_s3():
        conn = boto3.client("s3", region_name="eu-west-2")
        try:
            conn.head_bucket(Bucket=bucket_name)
        except ClientError:
            conn.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
            )
        yield conn
