from typing import Optional

from sqlalchemy import exc
from sqlalchemy.orm import Session

from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO
from app.repository import family_repo
from unit_tests.helpers.family import create_family_dto


def _maybe_throw():
    if getattr(family_repo, "throw_repository_error") is True:
        raise exc.SQLAlchemyError("bad repo")


def all(db: Session):
    return [create_family_dto("test")]


def get(db: Session, import_id: str) -> Optional[FamilyReadDTO]:
    _maybe_throw()
    if getattr(family_repo, "return_empty") is False:
        return create_family_dto(import_id)


def search(db: Session, query_params: dict[str, str]) -> list[FamilyReadDTO]:
    _maybe_throw()
    if getattr(family_repo, "return_empty") is False:
        return [create_family_dto("search1")]
    return []


def update(db: Session, import_id: str, family: FamilyWriteDTO, geo_id: int) -> bool:
    _maybe_throw()
    return getattr(family_repo, "return_empty") is False


def create(db: Session, family: FamilyCreateDTO, geo_id: int, org_id: int) -> str:
    _maybe_throw()
    return "" if getattr(family_repo, "return_empty") else "created"


def delete(db: Session, import_id: str) -> bool:
    _maybe_throw()
    return getattr(family_repo, "return_empty") is False


def count(db: Session) -> Optional[int]:
    _maybe_throw()
    if getattr(family_repo, "return_empty") is False:
        return 22
    return
