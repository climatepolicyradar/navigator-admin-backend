from app.main import app
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Get a TestClient instance that reads/write to the test database."""

    yield TestClient(app)
