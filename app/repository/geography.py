from typing import Optional
from sqlalchemy.orm import Session

from navigator_db_client.models.law_policy.geography import Geography


def get_id_from_value(db: Session, geo_string: str) -> Optional[int]:
    return db.query(Geography.id).filter_by(value=geo_string).scalar()
