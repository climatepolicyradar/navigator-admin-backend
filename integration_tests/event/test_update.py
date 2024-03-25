from datetime import datetime, timezone

from db_client.models.dfce import FamilyEvent
from db_client.models.dfce.family import EventStatus
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from integration_tests.setup_db import EXPECTED_EVENTS, setup_db
from unit_tests.helpers.event import create_event_write_dto


def _get_event_tuple(test_db: Session, import_id: str) -> FamilyEvent:
    fe: FamilyEvent = (
        test_db.query(FamilyEvent).filter(FamilyEvent.import_id == import_id).one()
    )
    assert fe is not None
    return fe


def test_update_event(client: TestClient, test_db: Session, user_header_token):
    setup_db(test_db)
    new_event = create_event_write_dto(title="Updated Title")
    response = client.put(
        "/api/v1/events/E.0.0.2",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Check the properties and values of the EventReadDTO object we return to the
    # client.
    assert data["event_type_value"] == "Amended"
    assert data["event_title"] == "Updated Title"
    assert isinstance(data["date"], str) is True
    assert data["date"] == "2023-01-01T00:00:00Z"

    # Get the record in the FamilyEvent table we want to update in the database and
    # check the types of the values are correct and that the values have been
    # successfully updated.
    fe = _get_event_tuple(test_db, "E.0.0.2")
    assert isinstance(fe.date, datetime) is True
    assert isinstance(fe.status, EventStatus) is True
    assert (
        isinstance(fe.family_document_import_id, str) is True
        or fe.family_document_import_id is None
    )
    assert (
        all(
            isinstance(x, str)
            for x in [
                fe.import_id,
                fe.family_import_id,
                fe.event_type_name,
                fe.title,
            ]
        )
        is True
    )
    assert fe.import_id == "E.0.0.2"
    assert fe.event_type_name == "Amended"
    assert fe.date == datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc)
    assert fe.title == "Updated Title"
    assert fe.family_import_id == "A.0.0.1"
    assert fe.family_document_import_id is None
    assert fe.status == EventStatus.OK


def test_update_event_when_not_authorised(client: TestClient, test_db: Session):
    setup_db(test_db)
    new_event = create_event_write_dto(
        title="Updated Title",
    )
    response = client.put("/api/v1/events/E.0.0.2", json=jsonable_encoder(new_event))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_event_idempotent(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    event = EXPECTED_EVENTS[1]
    response = client.put(
        f"/api/v1/events/{event['import_id']}",
        json=event,
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["event_title"] == EXPECTED_EVENTS[1]["event_title"]

    fe = _get_event_tuple(test_db, EXPECTED_EVENTS[1]["import_id"])
    assert fe.title == EXPECTED_EVENTS[1]["event_title"]


def test_update_event_rollback(
    client: TestClient, test_db: Session, rollback_event_repo, user_header_token
):
    setup_db(test_db)
    new_event = create_event_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/events/E.0.0.2",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    pd = _get_event_tuple(test_db, "E.0.0.2")
    assert pd.title != "Updated Title"

    assert rollback_event_repo.update.call_count == 1


def test_update_event_when_not_found(
    client: TestClient, test_db: Session, user_header_token
):
    setup_db(test_db)
    new_event = create_event_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/events/E.0.0.22",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Event not updated: E.0.0.22"


def test_update_event_when_db_error(
    client: TestClient, test_db: Session, bad_event_repo, user_header_token
):
    setup_db(test_db)

    new_event = create_event_write_dto(
        title="Updated Title",
    )
    response = client.put(
        "/api/v1/events/E.0.0.2",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_event_repo.update.call_count == 1
