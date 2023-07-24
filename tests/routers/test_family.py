from typing import Optional

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from app.model.family import FamilyDTO
import app.repository.family as family_repo


def get_family(import_id: str) -> FamilyDTO:
    return FamilyDTO(
        import_id=import_id,
        title="title",
        summary="summary",
        geography="geo",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )


def mock_get_family(import_id: str) -> Optional[FamilyDTO]:
    if import_id == "missing":
        return None
    return get_family(import_id)


def mock_search_families(q: str) -> list[FamilyDTO]:
    if q == "empty":
        return []
    else:
        return [get_family("search1")]


def mock_update_family(import_id: str, data: FamilyDTO) -> Optional[FamilyDTO]:
    if import_id != "missing":
        return data


def mock_create_family(data: FamilyDTO) -> Optional[FamilyDTO]:
    if data.import_id != "missing":
        return data


def test_get_family_uses_repo_200(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "get_family", mock_get_family)
    response = client.get(
        "/api/v1/families/import_id",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "import_id"


def test_get_family_uses_repo_404(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "get_family", mock_get_family)
    response = client.get(
        "/api/v1/families/missing",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not found: missing"


def test_search_family_uses_repo_200(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "search_families", mock_search_families)
    response = client.get(
        "/api/v1/families/?q=anything",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) > 0
    assert data[0]["import_id"] == "search1"


def test_search_family_uses_repo_404(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "search_families", mock_search_families)
    response = client.get(
        "/api/v1/families/?q=empty",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Families not found for term: empty"


def test_update_family_uses_repo_200(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "update_family", mock_update_family)
    new_data = get_family("fam1").dict()
    response = client.put("/api/v1/families/fam1", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "fam1"


def test_update_family_uses_repo_404(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "update_family", mock_update_family)
    new_data = get_family("fam1").dict()
    response = client.put("/api/v1/families/missing", json=new_data)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not updated: missing"


def test_create_family_uses_repo_200(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "create_family", mock_create_family)
    new_data = get_family("fam1").dict()
    response = client.post("/api/v1/families", json=new_data)
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "fam1"


def test_create_family_uses_repo_404(client: TestClient, monkeypatch: MonkeyPatch):
    monkeypatch.setattr(family_repo, "create_family", mock_create_family)
    new_data: FamilyDTO = get_family("fam1")
    new_data.import_id = "missing"
    response = client.post("/api/v1/families", json=new_data.dict())
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not created: missing"
