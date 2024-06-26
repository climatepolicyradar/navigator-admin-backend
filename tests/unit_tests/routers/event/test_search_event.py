import logging

from fastapi import status
from fastapi.testclient import TestClient


def test_search_when_ok(client: TestClient, event_service_mock, user_header_token):
    response = client.get("/api/v1/events/?q=anything", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"
    assert event_service_mock.search.call_count == 1


def test_search_when_invalid_params(
    client: TestClient, event_service_mock, user_header_token
):
    response = client.get("/api/v1/events/?wrong=yes", headers=user_header_token)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"
    assert event_service_mock.search.call_count == 0


def test_search_when_db_error(
    client: TestClient, event_service_mock, user_header_token
):
    event_service_mock.throw_repository_error = True
    response = client.get("/api/v1/events/?q=error", headers=user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "bad repo"
    assert event_service_mock.search.call_count == 1


def test_search_when_request_timeout(
    client: TestClient,
    event_service_mock,
    user_header_token,
    caplog,
):
    event_service_mock.throw_timeout_error = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/events/?q=timeout", headers=user_header_token)
    assert response.status_code == status.HTTP_408_REQUEST_TIMEOUT
    assert event_service_mock.search.call_count == 1
    assert (
        "Request timed out fetching matching events. Try adjusting your query."
        in caplog.text
    )


def test_search_when_not_found(
    client: TestClient, event_service_mock, user_header_token, caplog
):
    event_service_mock.missing = True
    with caplog.at_level(logging.INFO):
        response = client.get("/api/v1/events/?q=stuff", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    response.json()
    assert event_service_mock.search.call_count == 1
    assert (
        "Events not found for terms: {'q': 'stuff', 'max_results': 500}" in caplog.text
    )
