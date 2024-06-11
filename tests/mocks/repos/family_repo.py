from typing import Optional, Union

from sqlalchemy.orm import Session

from app.errors import RepositoryError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from app.repository import family_repo
from tests.helpers.family import create_family_read_dto


def _maybe_throw():
    if family_repo.throw_repository_error is True:
        raise RepositoryError("bad family repo")


def _maybe_timeout():
    if family_repo.throw_timeout_error is True:
        raise TimeoutError


def all(db: Session, org_id: Optional[int]):
    _maybe_throw()
    if family_repo.return_empty:
        return []
    return [create_family_read_dto("test", collections=["x.y.z.1", "x.y.z.2"])]


def get(db: Session, import_id: str) -> Optional[FamilyReadDTO]:
    _maybe_throw()
    if family_repo.return_empty is False:
        return create_family_read_dto(import_id, collections=["x.y.z.1", "x.y.z.2"])


def search(
    db: Session, query_params: dict[str, Union[str, int]], org_id: Optional[int]
) -> list[FamilyReadDTO]:
    _maybe_throw()
    _maybe_timeout()
    if family_repo.return_empty:
        return []
    if "title" in query_params.keys():
        return [create_family_read_dto("search1", collections=["x.y.z.1", "x.y.z.2"])]
    return [
        create_family_read_dto("search1", collections=["x.y.z.1", "x.y.z.2"]),
        create_family_read_dto("search2", collections=["x.y.z.1", "x.y.z.2"]),
    ]


def update(db: Session, import_id: str, family: FamilyWriteDTO, geo_id: int) -> bool:
    _maybe_throw()
    return family_repo.return_empty is False


def create(db: Session, family: FamilyCreateDTO, geo_id: int, org_id: int) -> str:
    _maybe_throw()
    return "" if family_repo.return_empty else "created"


def delete(db: Session, import_id: str) -> bool:
    _maybe_throw()
    return family_repo.return_empty is False


def count(db: Session, org_id: Optional[int]) -> Optional[int]:
    _maybe_throw()
    if family_repo.return_empty:
        return
    if family_repo.is_superuser:
        return 22
    return 11


def get_organisation(db: Session, family_import_id: str) -> Optional[int]:
    _maybe_throw()
    if family_repo.no_org:
        return None
    return 987 if family_repo.invalid_org else 1
