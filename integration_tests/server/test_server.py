import time
from fastapi.testclient import TestClient
import pytest
import asyncio
from fastapi import status
from httpx import AsyncClient
from app.main import app
from integration_tests.setup_db import setup_db

BASE_URL = "http://testserver"


@pytest.mark.asyncio
async def test_async_family_get(client: TestClient, test_db, user_header_token):
    # NOTE: We need the testclient fixture to monkeypatch the test_db too.
    setup_db(test_db)

    N_TIMES = 3
    start = time.time_ns()
    async with AsyncClient(app=app, base_url=BASE_URL) as async_client:
        responses = await asyncio.gather(
            *[
                async_client.get("/api/v1/families/A.0.0.1", headers=user_header_token)
                for _ in range(N_TIMES)
            ],
        )

    time_taken_ms = (time.time_ns() - start) / 1e6
    print(time_taken_ms)
    assert time_taken_ms < 500  # Assert that this takes less than 1 seconds

    # Check responses are all good
    assert len(responses) == N_TIMES
    for response in responses:
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_async_scenario(client: TestClient, test_db, user_header_token):
    # NOTE: We need the testclient fixture to monkeypatch the test_db too.
    setup_db(test_db)

    N_TIMES = 100
    N_REQUEST_LEN = 6
    start = time.thread_time_ns()
    async with AsyncClient(app=app, base_url=BASE_URL) as async_client:
        responses = await asyncio.gather(
            *[
                async_client.get("/api/v1/families/A.0.0.1", headers=user_header_token)
                for _ in range(N_TIMES)
            ],
            *[
                async_client.get("/api/v1/documents/D.0.0.1", headers=user_header_token)
                for _ in range(N_TIMES)
            ],
            *[
                async_client.get("/api/v1/documents/D.0.0.2", headers=user_header_token)
                for _ in range(N_TIMES)
            ],
            *[
                async_client.get("/api/v1/events/E.0.0.1", headers=user_header_token)
                for _ in range(N_TIMES)
            ],
            *[
                async_client.get("/api/v1/events/E.0.0.2", headers=user_header_token)
                for _ in range(N_TIMES)
            ],
            *[
                async_client.get("/api/v1/events/E.0.0.3", headers=user_header_token)
                for _ in range(N_TIMES)
            ],
        )

    time_taken_ns = time.thread_time_ns() - start
    assert time_taken_ns < 4e9  # Assert that this takes less than 4 seconds

    # Check responses are all good
    assert len(responses) == N_REQUEST_LEN * N_TIMES
    for response in responses:
        assert response.status_code == status.HTTP_200_OK
