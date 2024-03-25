from typing import Optional

from db_client.models.organisation.users import Organisation
from sqlalchemy.orm import Session


def get_id_from_name(db: Session, org_name: str) -> Optional[int]:
    return db.query(Organisation.id).filter_by(name=org_name).scalar()
