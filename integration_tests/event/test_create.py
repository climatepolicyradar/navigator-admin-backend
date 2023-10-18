from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session

from app.clients.db.models.law_policy import FamilyEvent, Family

from integration_tests.setup_db import setup_db
from unit_tests.helpers.event import create_event_create_dto


def test_create_event(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="A.0.0.1"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_family_event = (
        test_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id == created_import_id)
        .one()
    )

    assert actual_family_event is not None
    assert actual_family_event.title == "some event title"

    actual_family = (
        test_db.query(Family)
        .filter(Family.import_id == actual_family_event.family_import_id)
        .one()
    )
    assert actual_family is not None
    assert actual_family.title == "apple"


def test_create_event_when_not_authenticated(client: TestClient, test_db: Session):
    setup_db(test_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="A.0.0.3"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_event_rollback(
    client: TestClient, test_db: Session, rollback_event_repo, user_header_token
):
    setup_db(test_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="A.0.0.3"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_fd = (
        test_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id == "A.0.0.9")
        .one_or_none()
    )
    assert actual_fd is None
    assert rollback_event_repo.create.call_count == 1


def test_create_event_when_db_error(
    client: TestClient, test_db: Session, bad_event_repo, user_header_token
):
    setup_db(test_db)
    new_event = create_event_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_event_repo.create.call_count == 1


def test_create_event_when_family_invalid(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="invalid"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "The import id invalid is invalid!"


def test_create_event_when_family_missing(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_event = create_event_create_dto(
        title="some event title",
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == f"Could not find event for {new_event.family_import_id}"
