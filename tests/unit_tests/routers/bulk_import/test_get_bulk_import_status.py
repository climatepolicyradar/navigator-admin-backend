from unittest.mock import patch
from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient

from app.model.bulk_import import BulkImportStatus, BulkImportStatusDTO

TEST_IMPORT_ID = UUID("11111111-1111-1111-1111-111111111111")
STATUS_URL = f"/api/v1/bulk-import/status/{TEST_IMPORT_ID}"


def test_get_bulk_import_status_when_not_authenticated(client: TestClient):
    response = client.get(STATUS_URL)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_bulk_import_status_when_non_admin_non_super(
    client: TestClient, user_header_token
):
    response = client.get(STATUS_URL, headers=user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_bulk_import_status_when_admin_non_super(
    client: TestClient, admin_user_header_token
):
    response = client.get(STATUS_URL, headers=admin_user_header_token)
    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch("app.api.api_v1.routers.bulk_import.get_import_status")
def test_get_bulk_import_status_when_running(
    mock_get_import_status, client: TestClient, superuser_header_token
):
    mock_get_import_status.return_value = BulkImportStatusDTO(
        import_id=str(TEST_IMPORT_ID),
        status=BulkImportStatus.RUNNING,
    )

    response = client.get(STATUS_URL, headers=superuser_header_token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "running"
    assert response.json()["counts"] is None


@patch("app.api.api_v1.routers.bulk_import.get_import_status")
def test_get_bulk_import_status_when_succeeded(
    mock_get_import_status, client: TestClient, superuser_header_token
):
    mock_get_import_status.return_value = BulkImportStatusDTO(
        import_id=str(TEST_IMPORT_ID),
        status=BulkImportStatus.SUCCESS,
        counts={"collections": 0, "families": 1, "documents": 2, "events": 3},
    )

    response = client.get(STATUS_URL, headers=superuser_header_token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "success"
    assert response.json()["counts"] == {
        "collections": 0,
        "families": 1,
        "documents": 2,
        "events": 3,
    }


@patch("app.api.api_v1.routers.bulk_import.get_import_status")
def test_get_bulk_import_status_when_failed(
    mock_get_import_status, client: TestClient, superuser_header_token
):
    mock_get_import_status.return_value = BulkImportStatusDTO(
        import_id=str(TEST_IMPORT_ID),
        status=BulkImportStatus.FAILURE,
        error="bad data",
    )

    response = client.get(STATUS_URL, headers=superuser_header_token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "failure"
    assert response.json()["error"] == "bad data"


def test_get_bulk_import_status_when_import_id_not_a_uuid(
    client: TestClient, superuser_header_token
):
    response = client.get(
        "/api/v1/bulk-import/status/not-a-uuid", headers=superuser_header_token
    )
    assert response.status_code == 422
