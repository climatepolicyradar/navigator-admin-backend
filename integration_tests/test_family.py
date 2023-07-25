from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models.law_policy.family import Family, FamilyCategory


def _setup_db(test_db: Session):
    with open("integration_tests/default-data.sql") as file:
        query = text(file.read())
        test_db.execute(query)

    test_db.add(
        Family(
            import_id="A.0.0.1",
            title="title",
            description="",
            geography_id=1,
            family_category=FamilyCategory.UNFCCC,
        )
    )

    test_db.commit()


def test_get_all_families_uses_service_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    n = test_db.query(Family).count()
    assert n > 0
    response = client.get(
        "/api/v1/families",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "A.0.0.1"
