from typing import Optional

from db_client.models.organisation.corpus import Corpus
from sqlalchemy.orm import Session

from app.errors import ValidationError
from app.repository import corpus_repo


def get_corpus_org_id(db: Session, corpus_import_id: str) -> Optional[int]:
    org_id = corpus_repo.get_corpus_org_id(db, corpus_import_id)
    return org_id


def validate(import_id: str) -> str:
    try:
        return Corpus(import_id).corpus_import_id
    except ValueError as e:
        raise ValidationError(str(e))
