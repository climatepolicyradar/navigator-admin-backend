from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models.law_policy.family import Family, FamilyCategory
from unit_tests.helpers.family import create_family_dto


def _setup_db(test_db: Session):
    with open("integration_tests/default-data.sql") as file:
        query = text(file.read())
        test_db.execute(query)

    FAMILY_1 = Family(
        import_id="A.0.0.1",
        title="apple",
        description="",
        geography_id=1,
        family_category=FamilyCategory.UNFCCC,
    )

    FAMILY_2 = Family(
        import_id="A.0.0.2",
        title="apple orange banana",
        description="",
        geography_id=1,
        family_category=FamilyCategory.UNFCCC,
    )

    FAMILY_3 = Family(
        import_id="A.0.0.3",
        title="title",
        description="orange peas",
        geography_id=1,
        family_category=FamilyCategory.UNFCCC,
    )

    test_db.add(FAMILY_1)
    test_db.add(FAMILY_2)
    test_db.add(FAMILY_3)
    test_db.commit()


# --- GET ALL


def test_get_all_families_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) == 3
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["A.0.0.1", "A.0.0.2", "A.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])


# --- GET


def test_get_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A.0.0.1",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "A.0.0.1"


def test_get_family_404(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not found: A.0.0.8"


def test_get_family_400(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A008",
    )
    assert response.status_code == 400
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_family_503(client: TestClient, test_db: Session, bad_family_repo):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
    )
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"


# --- SEARCH


def test_search_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=orange",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 2

    expected_ids = set(["A.0.0.2", "A.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_404(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=chicken",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Families not found for term: chicken"


# --- UPDATE


def test_update_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.2",
        title="Updated Title",
        summary="just a test",
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["summary"] == "just a test"

    db_family: Family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title == "Updated Title"
    assert db_family.description == "just a test"


def test_update_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo
):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.2",
        title="Updated Title",
        summary="just a test",
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503

    db_family: Family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title != "Updated Title"
    assert db_family.description != "just a test"


def test_update_family_404(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not updated: A.0.0.22"


def test_update_family_503(client: TestClient, test_db: Session, bad_family_repo):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_update_family__invalid_geo_400(
    client: TestClient, test_db: Session, bad_family_repo
):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
    )
    new_family.geography = "UK"
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


# --- CREATE


def test_create_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Title"
    assert data["summary"] == "test test test"
    actual_family = test_db.query(Family).filter(Family.import_id == "A.0.0.9").one()
    assert actual_family.title == "Title"
    assert actual_family.description == "test test test"


def test_create_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo
):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503
    actual_family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.9").one_or_none()
    )
    assert actual_family is None


def test_create_family_503(client: TestClient, test_db: Session, bad_family_repo):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_create_family__invalid_geo_400(
    client: TestClient, test_db: Session, bad_family_repo
):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    new_family.geography = "UK"
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


# --- DELETE


def test_delete_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2",
    )
    assert response.status_code == 200
    n = test_db.query(Family).count()
    assert n == 2


def test_delete_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo
):
    _setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2",
    )
    assert response.status_code == 503
    n = test_db.query(Family).count()
    assert n == 3


def test_delete_family_404(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.delete("/api/v1/families/A.0.0.22")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not deleted: A.0.0.22"


def test_delete_family_503(client: TestClient, test_db: Session, bad_family_repo):
    _setup_db(test_db)
    response = client.delete("/api/v1/families/A.0.0.1")
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"
