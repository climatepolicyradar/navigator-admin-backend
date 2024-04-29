from typing import Optional, Union

from sqlalchemy.orm import Session

from app.errors import RepositoryError
from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from app.repository import family_repo
from tests.helpers.family import create_family_read_dto


def _maybe_throw():
    if family_repo.throw_repository_error is True:
        raise RepositoryError("bad repo")


def _maybe_timeout():
    if family_repo.throw_timeout_error is True:
        raise TimeoutError


def all(db: Session):
    return [create_family_read_dto("test")]


def get(db: Session, import_id: str) -> Optional[FamilyReadDTO]:
    _maybe_throw()
    if family_repo.return_empty is False:
        return create_family_read_dto(import_id)


def search(
    db: Session, query_params: dict[str, Union[str, int]]
) -> list[FamilyReadDTO]:
    _maybe_throw()
    _maybe_timeout()
    if family_repo.return_empty:
        return []
    if "title" in query_params.keys():
        return [create_family_read_dto("search1")]
    return [create_family_read_dto("search1"), create_family_read_dto("search2")]


def update(db: Session, import_id: str, family: FamilyWriteDTO, geo_id: int) -> bool:
    _maybe_throw()
    return family_repo.return_empty is False


def create(db: Session, family: FamilyCreateDTO, geo_id: int, org_id: int) -> str:
    _maybe_throw()
    return "" if family_repo.return_empty else "created"


def delete(db: Session, import_id: str) -> bool:
    _maybe_throw()
    return family_repo.return_empty is False


def count(db: Session) -> Optional[int]:
    _maybe_throw()
    if family_repo.return_empty is False:
        return 22
    return
