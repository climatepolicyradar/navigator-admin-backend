"""
Family Service

This file hands off to the family repo, adding the dependency of the db (future)
"""
from typing import Optional
from app.model.family import FamilyDTO
import app.repository.family as family_repo
import app.db.session as db_session


def get(import_id: str) -> Optional[FamilyDTO]:
    return family_repo.get(import_id)


def all() -> list[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.all(db)


def search(search_term: str) -> Optional[list[FamilyDTO]]:
    return family_repo.search(search_term)


def update(import_id: str, family: FamilyDTO) -> Optional[FamilyDTO]:
    return family_repo.update(import_id, family)


def create(family: FamilyDTO) -> Optional[FamilyDTO]:
    return family_repo.create(family)


def delete(import_id: str) -> bool:
    return family_repo.delete(import_id)
