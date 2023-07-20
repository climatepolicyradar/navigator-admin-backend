from typing import Optional
from app.model.family import FamilyResponse
import app.repository.family as family_repo


def mock_get_family(import_id: str) -> Optional[FamilyResponse]:
    if import_id == "missing":
        return None

    return FamilyResponse(
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


def test_get_family_ok(client, monkeypatch):
    monkeypatch.setattr(family_repo, "get_family", mock_get_family)
    response = client.get(
        "/api/v1/families/import_id",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "import_id"


def test_get_family_not_found(client, monkeypatch):
    monkeypatch.setattr(family_repo, "get_family", mock_get_family)
    response = client.get(
        "/api/v1/families/missing",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not found: missing"
