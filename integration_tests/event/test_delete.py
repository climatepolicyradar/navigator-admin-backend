from db_client.models.law_policy import FamilyEvent
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.repository.event as event_repo
from integration_tests.setup_db import setup_db


def test_delete_event(client: TestClient, test_db: Session, admin_user_header_token):
    setup_db(test_db)
    response = client.delete("/api/v1/events/E.0.0.2", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_200_OK
    assert test_db.query(FamilyEvent).count() == 2
    assert (
        test_db.query(FamilyEvent).filter(FamilyEvent.import_id == "E.0.0.2").count()
        == 0
    )


def test_delete_event_when_not_authenticated(
    client: TestClient, test_db: Session, mocker
):
    setup_db(test_db)
    mocker.spy(event_repo, "delete")
    response = client.delete(
        "/api/v1/events/E.0.0.2",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert test_db.query(FamilyEvent).count() == 3
    assert event_repo.delete.call_count == 0


def test_delete_event_rollback(
    client: TestClient,
    test_db: Session,
    rollback_event_repo,
    admin_user_header_token,
):
    setup_db(test_db)
    response = client.delete("/api/v1/events/E.0.0.2", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert test_db.query(FamilyEvent).count() == 3
    assert (
        test_db.query(FamilyEvent).filter(FamilyEvent.import_id == "E.0.0.2").count()
        == 1
    )
    assert rollback_event_repo.delete.call_count == 1


def test_delete_event_when_not_found(
    client: TestClient, test_db: Session, admin_user_header_token
):
    setup_db(test_db)
    response = client.delete("/api/v1/events/E.0.0.22", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not deleted: E.0.0.22"
    assert test_db.query(FamilyEvent).count() == 3
    assert (
        test_db.query(FamilyEvent).filter(FamilyEvent.import_id == "E.0.0.22").count()
        == 0
    )


def test_delete_event_when_db_error(
    client: TestClient, test_db: Session, bad_event_repo, admin_user_header_token
):
    setup_db(test_db)
    response = client.delete("/api/v1/events/E.0.0.1", headers=admin_user_header_token)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_event_repo.delete.call_count == 1
