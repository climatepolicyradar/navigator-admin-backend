"""
Family Service

This file hands off to the family repo, adding the dependency of the db (future)
"""
from typing import Optional
from app.model.family import FamilyDTO
import app.repository.family as clean_family_repo


def get(import_id: str) -> Optional[FamilyDTO]:
    return clean_family_repo.get(import_id)


def all() -> list[FamilyDTO]:
    return clean_family_repo.all()


def search(search_term: str) -> Optional[list[FamilyDTO]]:
    return clean_family_repo.search(search_term)


def update(import_id: str, family: FamilyDTO) -> Optional[FamilyDTO]:
    return clean_family_repo.update(import_id, family)


def create(family: FamilyDTO) -> Optional[FamilyDTO]:
    return clean_family_repo.create(family)


def delete(import_id: str) -> bool:
    return clean_family_repo.delete(import_id)
