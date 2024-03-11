from typing import Optional

from db_client.models.law_policy.geography import Geography
from sqlalchemy.orm import Session


def get_id_from_value(db: Session, geo_string: str) -> Optional[int]:
    return db.query(Geography.id).filter_by(value=geo_string).scalar()
