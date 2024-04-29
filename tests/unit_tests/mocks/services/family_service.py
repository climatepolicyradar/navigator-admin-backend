from typing import Optional

from pytest import MonkeyPatch

from app.errors import RepositoryError, ValidationError
from app.model.family import FamilyReadDTO, FamilyWriteDTO
from tests.helpers.family import create_family_read_dto


def mock_family_service(family_service, monkeypatch: MonkeyPatch, mocker):
    family_service.missing = False
    family_service.invalid_collections = False
    family_service.throw_repository_error = False
    family_service.throw_validation_error = False
    family_service.throw_timeout_error = False

    def maybe_throw():
        if family_service.throw_repository_error:
            raise RepositoryError("bad repo")
        if family_service.throw_validation_error:
            raise ValidationError("invalid")

    def maybe_timeout():
        if family_service.throw_timeout_error:
            raise TimeoutError

    def mock_get_all_families():
        return [create_family_read_dto("test")]

    def mock_get_family(import_id: str) -> Optional[FamilyReadDTO]:
        if not family_service.missing:
            return create_family_read_dto(import_id)

    def mock_search_families(q_params: dict) -> list[FamilyReadDTO]:
        if q_params["q"] == "empty":
            return []

        maybe_throw()
        maybe_timeout()
        return [create_family_read_dto("search1")]

    def mock_update_family(
        import_id: str, user_email: str, data: FamilyWriteDTO
    ) -> Optional[FamilyReadDTO]:
        if not family_service.missing:
            return create_family_read_dto(
                import_id,
                data.title,
                data.summary,
                data.geography,
                data.category,
                data.metadata,
                "slug",
                ["col2", "col3"],
            )

    def mock_create_family(data: FamilyWriteDTO, user_email: str) -> str:
        if family_service.missing:
            raise RepositoryError("bad-db")
        return "new-import-id"

    def mock_delete_family(import_id: str, user_email: str) -> Optional[bool]:
        maybe_throw()
        return not family_service.missing

    def mock_count_collection() -> Optional[int]:
        maybe_throw()
        if family_service.missing:
            return None
        return 22

    monkeypatch.setattr(family_service, "get", mock_get_family)
    mocker.spy(family_service, "get")

    monkeypatch.setattr(family_service, "all", mock_get_all_families)
    mocker.spy(family_service, "all")

    monkeypatch.setattr(family_service, "search", mock_search_families)
    mocker.spy(family_service, "search")

    monkeypatch.setattr(family_service, "update", mock_update_family)
    mocker.spy(family_service, "update")

    monkeypatch.setattr(family_service, "create", mock_create_family)
    mocker.spy(family_service, "create")

    monkeypatch.setattr(family_service, "delete", mock_delete_family)
    mocker.spy(family_service, "delete")

    monkeypatch.setattr(family_service, "count", mock_count_collection)
    mocker.spy(family_service, "count")
