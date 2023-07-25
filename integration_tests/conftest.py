import uuid
from fastapi.testclient import TestClient
import pytest
from app.config import SQLALCHEMY_DATABASE_URI
from sqlalchemy_utils import create_database, database_exists, drop_database
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.db.session as db_session
from app.main import app


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
