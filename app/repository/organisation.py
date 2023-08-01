from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.app.users import Organisation


def get_id_from_name(db: Session, org_name: str) -> Optional[int]:
    return db.query(Organisation.id).filter_by(name=org_name).scalar()
