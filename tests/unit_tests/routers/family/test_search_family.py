"""
Tests the routes for family management.

This uses a service mock and ensures each endpoint calls into the service.
"""

import logging

from fastapi import status
from fastapi.testclient import TestClient


def test_search_when_ok(client: TestClient, family_service_mock, user_header_token):
    response = client.get("/api/v1/families/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert family_service_mock.search.call_count == 1


def test_search_when_invalid_params(
    client: TestClient, family_service_mock, user_header_token
):
    response = client.get("/api/v1/families/?wrong=yes", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
    assert family_service_mock.search.call_count == 0


def test_search_when_db_error(
    client: TestClient, family_service_mock, user_header_token
):
    family_service_mock.throw_repository_error = True
    response = client.get("/api/v1/families/?q=error", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "bad repo"
    assert family_service_mock.search.call_count == 1


def test_search_when_request_timeout(
    client: TestClient, family_service_mock, user_header_token, caplog
):
    family_service_mock.throw_timeout_error = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/families/?q=timeout", headers=user_header_token)
    assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
    assert family_service_mock.search.call_count == 1
    assert (
        "Request timed out fetching matching families. Try adjusting your query."
        in caplog.text
    )


def test_search_when_not_found(
    client: TestClient, family_service_mock, user_header_token, caplog
):
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/families/?q=empty", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    response.json()
    assert family_service_mock.search.call_count == 1
    assert (
        "Families not found for terms: {'q': 'empty', 'max_results': 500}"
        in caplog.text
    )
