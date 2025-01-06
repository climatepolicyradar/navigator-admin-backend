from typing import Optional

from db_client.models.organisation.users import Organisation
from sqlalchemy.orm import Session


def get_id_from_name(db: Session, org_name: str) -> Optional[int]:
    return db.query(Organisation.id).filter_by(name=org_name).scalar()


def get_name_from_id(db: Session, org_id: int) -> Optional[str]:
    return db.query(Organisation.name).filter_by(id=org_id).scalar()


def get_distinct_org_options(db: Session) -> list[str]:
    query = db.query(Organisation).all()

    # Combine organisation_type values with name unique values into a single list.
    org_names = [org.name for org in query]
    org_types = [org.organisation_type for org in query]
    options = list(set(org_names + org_types))
    return options
