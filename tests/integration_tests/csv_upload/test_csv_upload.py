from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.service.csv_upload import DATA_PROVIDER_COLUMN, EXPECTED_COLUMNS

PATCH_TARGET = "app.api.api_v1.routers.csv_upload.upload_csv_to_s3"


def _csv_bytes(columns: list[str], provider: str = "CapsuleCorp") -> bytes:
    row = [provider if col == DATA_PROVIDER_COLUMN else "x" for col in columns]
    return f"{','.join(columns)}\n{','.join(row)}\n".encode()


def test_csv_upload_returns_unprocessable_entity_when_required_column_missing(
    client: TestClient,
    superuser_header_token,
):
    missing_column = EXPECTED_COLUMNS[-1]
    columns = [col for col in EXPECTED_COLUMNS if col != missing_column]

    response = client.post(
        "/api/v1/csv-upload",
        files={"file": ("upload.csv", _csv_bytes(columns), "text/csv")},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {"detail": f"Missing required columns: {missing_column}"}


def test_csv_upload_returns_unprocessable_entity_when_data_provider_empty(
    client: TestClient,
    superuser_header_token,
):
    content = _csv_bytes(list(EXPECTED_COLUMNS), provider="")

    response = client.post(
        "/api/v1/csv-upload",
        files={"file": ("upload.csv", content, "text/csv")},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {
        "detail": f"'{DATA_PROVIDER_COLUMN}' must not be empty in the first row."
    }


def test_csv_upload_returns_unprocessable_entity_when_columns_in_wrong_order(
    client: TestClient,
    superuser_header_token,
):
    columns = list(EXPECTED_COLUMNS)
    columns[0], columns[1] = columns[1], columns[0]

    response = client.post(
        "/api/v1/csv-upload",
        files={"file": ("upload.csv", _csv_bytes(columns), "text/csv")},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "wrong order" in response.json()["detail"]


def test_csv_upload_returns_unprocessable_entity_when_column_duplicated(
    client: TestClient,
    superuser_header_token,
):
    duplicated_column = EXPECTED_COLUMNS[0]
    columns = [*EXPECTED_COLUMNS, duplicated_column]

    response = client.post(
        "/api/v1/csv-upload",
        files={"file": ("upload.csv", _csv_bytes(columns), "text/csv")},
        headers=superuser_header_token,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert response.json() == {"detail": f"Duplicate columns: {duplicated_column}"}


def test_csv_upload_returns_s3_key_when_valid(
    client: TestClient,
    superuser_header_token,
):
    s3_key = "uploads/upload.csv"
    content = _csv_bytes(list(EXPECTED_COLUMNS))

    with patch(PATCH_TARGET, return_value=s3_key):
        response = client.post(
            "/api/v1/csv-upload",
            files={"file": ("upload.csv", content, "text/csv")},
            headers=superuser_header_token,
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "CSV uploaded successfully", "key": s3_key}
