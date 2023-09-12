from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy.orm import Session
from app.db.models.law_policy.family import Family
from integration_tests.setup_db import setup_db


def test_delete_family(client: TestClient, test_db: Session, admin_user_header_token):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == status.HTTP_200_OK
    n = test_db.query(Family).count()
    assert n == 2


def test_delete_family_is_authed(client: TestClient, test_db: Session):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo, admin_user_header_token
):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == 503
    n = test_db.query(Family).count()
    assert n == 3


def test_delete_family_404(
    client: TestClient, test_db: Session, admin_user_header_token
):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.22", headers=admin_user_header_token
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not deleted: A.0.0.22"


def test_delete_family_503(
    client: TestClient, test_db: Session, bad_family_repo, admin_user_header_token
):
    setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.1", headers=admin_user_header_token
    )
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"
