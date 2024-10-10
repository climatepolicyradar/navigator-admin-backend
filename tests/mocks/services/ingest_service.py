from typing import Any

from pytest import MonkeyPatch

from app.errors import RepositoryError


def mock_ingest_service(ingest_service, monkeypatch: MonkeyPatch, mocker):
    ingest_service.throw_repository_error = False

    def maybe_throw():
        if ingest_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_import_data(
        data: dict[str, Any], corpus_import_id: str
    ) -> dict[str, list[str]]:
        maybe_throw()

        collection_data = data["collections"] if "collections" in data else None
        family_data = data["families"] if "families" in data else None
        document_data = data["documents"] if "documents" in data else None
        event_data = data["events"] if "events" in data else None

        response = {"collections": [], "families": [], "documents": [], "events": []}

        if collection_data:
            for coll in collection_data:
                response["collections"].append(coll["import_id"])
        if family_data:
            for fam in family_data:
                response["families"].append(fam["import_id"])
        if document_data:
            for doc in document_data:
                response["documents"].append(doc["import_id"])
        if event_data:
            for ev in event_data:
                response["events"].append(ev["import_id"])

        return response

    monkeypatch.setattr(ingest_service, "import_data", mock_import_data)
    mocker.spy(ingest_service, "import_data")
