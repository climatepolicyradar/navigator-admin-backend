import importlib
import sys
from app.main import app
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Get a TestClient instance that reads/write to the test database."""

    yield TestClient(app)


@pytest.fixture()
def family_repo():
    """Resets the repo while we have an in-memory one."""
    module = "app.repository.family"
    mod = importlib.import_module(module)
    yield mod
    del sys.modules[module]
