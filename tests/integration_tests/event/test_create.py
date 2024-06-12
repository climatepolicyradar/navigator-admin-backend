from db_client.models.dfce import Family, FamilyEvent
from db_client.models.dfce.family import EventStatus
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.event import create_event_create_dto
from tests.integration_tests.setup_db import setup_db


def test_create_event(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
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
        data_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id == created_import_id)
        .one()
    )

    assert actual_family_event is not None
    assert actual_family_event.title == "some event title"

    actual_family = (
        data_db.query(Family)
        .filter(Family.import_id == actual_family_event.family_import_id)
        .one()
    )
    assert actual_family is not None
    assert actual_family.title == "apple"


def test_create_event_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="A.0.0.3"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_event_rollback(
    client: TestClient,
    data_db: Session,
    rollback_event_repo,
    non_cclw_user_header_token,
):
    setup_db(data_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="A.0.0.3"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    actual_fd = (
        data_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id == "A.0.0.9")
        .one_or_none()
    )
    assert actual_fd is None
    assert rollback_event_repo.create.call_count == 1


def test_create_event_when_db_error(
    client: TestClient, data_db: Session, bad_event_repo, non_cclw_user_header_token
):
    setup_db(data_db)
    new_event = create_event_create_dto(title="Title", family_import_id="A.0.0.3")
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_event_repo.create.call_count == 1


def test_create_event_when_family_invalid(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
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
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
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
    assert (
        data["detail"]
        == f"Could not find family when creating event for {new_event.family_import_id}"
    )


def test_event_status_is_created_on_create(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="A.0.0.3"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_201_CREATED
    created_import_id = response.json()
    actual_fe = (
        data_db.query(FamilyEvent)
        .filter(FamilyEvent.import_id == created_import_id)
        .one()
    )

    assert actual_fe is not None
    assert actual_fe.status is EventStatus.OK


def test_create_event_when_org_mismatch(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    new_event = create_event_create_dto(
        title="some event title", family_import_id="A.0.0.3"
    )
    response = client.post(
        "/api/v1/events",
        json=jsonable_encoder(new_event),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
