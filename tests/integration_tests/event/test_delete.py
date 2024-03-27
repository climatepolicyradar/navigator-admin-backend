from db_client.models.dfce import FamilyEvent
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db


def test_delete_event(client: TestClient, data_db: Session, admin_user_header_token):
    setup_db(data_db)
    response = client.delete("/api/v1/events/E.0.0.2", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert data_db.query(FamilyEvent).count() == 2
    assert (
        data_db.query(FamilyEvent).filter(FamilyEvent.import_id == "E.0.0.2").count()
        == 0
    )


def test_delete_event_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.delete(
        "/api/v1/events/E.0.0.2",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert data_db.query(FamilyEvent).count() == 3


def test_delete_event_rollback(
    client: TestClient,
    data_db: Session,
    rollback_event_repo,
    admin_user_header_token,
):
    setup_db(data_db)
    response = client.delete("/api/v1/events/E.0.0.2", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert data_db.query(FamilyEvent).count() == 3
    assert (
        data_db.query(FamilyEvent).filter(FamilyEvent.import_id == "E.0.0.2").count()
        == 1
    )
    assert rollback_event_repo.delete.call_count == 1


def test_delete_event_when_not_found(
    client: TestClient, data_db: Session, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete("/api/v1/events/E.0.0.22", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not deleted: E.0.0.22"
    assert data_db.query(FamilyEvent).count() == 3
    assert (
        data_db.query(FamilyEvent).filter(FamilyEvent.import_id == "E.0.0.22").count()
        == 0
    )


def test_delete_event_when_db_error(
    client: TestClient, data_db: Session, bad_event_repo, admin_user_header_token
):
    setup_db(data_db)
    response = client.delete("/api/v1/events/E.0.0.1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_event_repo.delete.call_count == 1
