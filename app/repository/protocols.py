from typing import Optional, Protocol, Union
from sqlalchemy.orm import Session

from app.model.family import FamilyCreateDTO, FamilyReadDTO, FamilyWriteDTO


class FamilyRepo(Protocol):
    """The interface definition for a FamilyRepo"""

    @staticmethod
    def all(db: Session) -> list[FamilyReadDTO]:
        """Returns all the families"""
        ...

    @staticmethod
    def get(db: Session, import_id: str) -> Optional[FamilyReadDTO]:
        """Gets a single family"""
        ...

    @staticmethod
    def search(
        db: Session, query_params: dict[str, Union[str, int]]
    ) -> list[FamilyReadDTO]:
        """Searches the families"""
        ...

    @staticmethod
    def update(
        db: Session, import_id: str, family: FamilyWriteDTO, geo_id: int
    ) -> bool:
        """Updates a family"""
        ...

    @staticmethod
    def create(db: Session, family: FamilyCreateDTO, geo_id: int, org_id: int) -> str:
        """Creates a family"""
        ...

    @staticmethod
    def delete(db: Session, import_id: str) -> bool:
        """Deletes a family"""
        ...

    @staticmethod
    def count(db: Session) -> Optional[int]:
        """Counts all the families"""
        ...
