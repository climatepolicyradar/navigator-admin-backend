"""
Family Service

This file hands off to the family repo, adding the dependency of the db (future)
"""
from typing import Optional
from app.model.family import FamilyDTO
import app.repository.family as family_repo
import app.db.session as db_session


def get(import_id: str) -> Optional[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.get(db, import_id)


def all() -> list[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.all(db)


def search(search_term: str) -> list[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.search(db, search_term)


def update(family: FamilyDTO) -> Optional[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.update(db, family)


def create(family: FamilyDTO) -> Optional[FamilyDTO]:
    db = db_session.get_db()
    return family_repo.create(db, family)


def delete(import_id: str) -> bool:
    db = db_session.get_db()
    return family_repo.delete(db, import_id)
