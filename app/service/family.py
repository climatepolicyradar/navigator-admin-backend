"""
Family Service

This file hands off to the family repo, adding the dependency of the db (future)
"""
from typing import Optional
from app.model.family import FamilyDTO
import app.repository.family as family_repo


def get_family(import_id: str) -> Optional[FamilyDTO]:
    return family_repo.get_family(import_id)


def get_all_families() -> list[FamilyDTO]:
    return family_repo.get_all_families()


def search_families(search_term: str) -> Optional[list[FamilyDTO]]:
    return family_repo.search_families(search_term)


def update_family(import_id: str, family: FamilyDTO) -> Optional[FamilyDTO]:
    return family_repo.update_family(import_id, family)


def create_family(family: FamilyDTO) -> Optional[FamilyDTO]:
    return family_repo.create_family(family)


def delete_family(import_id: str) -> bool:
    return family_repo.delete_family(import_id)
