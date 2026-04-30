from datetime import datetime, timezone

from db_client.models.dfce import EventStatus, FamilyDocument, FamilyEvent
from db_client.models.dfce.family import DocumentStatus
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.helpers.utils import remove_trigger_cols_from_result
from tests.integration_tests.setup_db import EXPECTED_FAMILIES, add_data, setup_db


def test_get_family(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["import_id"] == "A.0.0.1"

    actual_data = remove_trigger_cols_from_result(data)
    assert actual_data == EXPECTED_FAMILIES[0]


def test_get_family_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.1",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_family_when_not_found(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "Family not found: A.0.0.8"


def test_get_family_when_invalid_id(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A008",
        headers=user_header_token,
    )
    assert response.status_code == 400
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_family_when_db_error(
    client: TestClient, data_db: Session, bad_family_repo, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_search_retrieves_families_without_geographies(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    add_data(
        data_db,
        [
            {
                "import_id": "A.0.0.12",
                "title": "title",
                "summary": "gregarious magazine rub",
                "geography": "",
                "geographies": [],
                "category": "UNFCCC",
                "status": "Created",
                "metadata": {"author": ["CPR"], "author_type": ["Party"]},
                "organisation": "UNFCCC",
                "corpus_import_id": "UNFCCC.corpus.i00000001.n0000",
                "corpus_title": "UNFCCC Submissions",
                "corpus_type": "Intl. agreements",
                "slug": "Slug4",
                "events": ["E.0.0.3"],
                "published_date": "2018-12-24T04:59:33Z",
                "last_updated_date": "2018-12-24T04:59:33Z",
                "documents": ["D.0.0.1", "D.0.0.2"],
                "collections": ["C.0.0.4"],
                "concepts": [],
            },
        ],
    )

    response = client.get(
        "/api/v1/families/A.0.0.12",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data is not None


def test_get_family_excludes_deleted_documents_and_their_events(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    deleted_doc = (
        data_db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == "D.0.0.1")
        .one()
    )
    deleted_doc.document_status = DocumentStatus.DELETED
    data_db.add(deleted_doc)
    data_db.add(
        FamilyEvent(
            import_id="E.0.0.99",
            title="Deleted document event",
            date=datetime(2018, 12, 25, tzinfo=timezone.utc),
            event_type_name="Deleted Doc Event",
            family_import_id=deleted_doc.family_import_id,
            family_document_import_id=deleted_doc.import_id,
            status=EventStatus.OK,
            valid_metadata={
                "event_type": ["Deleted Doc Event"],
                "datetime_event_name": ["Deleted Doc Event"],
            },
        )
    )
    data_db.commit()

    response = client.get(
        "/api/v1/families/A.0.0.1",
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "D.0.0.1" not in data["documents"]
    assert "E.0.0.99" not in data["events"]
