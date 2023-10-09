"""
Tests the analytics routes.

This uses a service mock and ensures each endpoint calls into the service.
"""
from fastapi import status
from fastapi.testclient import TestClient


def test_get_all_when_ok(client: TestClient, analytics_service_mock, user_header_token):
    response = client.get("/api/v1/analytics/summary", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert type(data) is dict
    assert len(data) == 4
    assert data["n_events"] == 0
    assert analytics_service_mock.summary.call_count == 1


def test_get_when_ok(client: TestClient, analytics_service_mock, user_header_token):
    response = client.get("/api/v1/analytics/summary", headers=user_header_token)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["n_events"] == 0
    assert analytics_service_mock.summary.call_count == 1


def test_get_when_not_found(
    client: TestClient, analytics_service_mock, user_header_token
):
    analytics_service_mock.return_empty = True
    response = client.get("/api/v1/analytics/summary", headers=user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Analytics summary not found"
    assert analytics_service_mock.summary.call_count == 1
