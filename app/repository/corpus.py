from typing import Optional

from db_client.models.organisation.corpus import Corpus
from sqlalchemy.orm import Session


def get_corpus_org_id(db: Session, corpus_id: str) -> Optional[int]:
    return db.query(Corpus.organisation_id).filter_by(id=corpus_id).scalar()
