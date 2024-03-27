from typing import Optional

from db_client.models.organisation import Corpus, CorpusType
from sqlalchemy.orm import Session

from app.model.general import Json


def get_schema_for_org(db: Session, org_id: int) -> Optional[Json]:
    """
    Gets the schema for an organisation.

    TODO: Remove assumption:
    https://linear.app/climate-policy-radar/issue/PDCT-1011
    """
    corpus_type = (
        db.query(CorpusType)
        .join(
            Corpus,
            Corpus.corpus_type_name == CorpusType.name,
        )
        .filter(Corpus.organisation_id == org_id)
        .one_or_none()
    )
    if corpus_type is not None:
        return corpus_type.valid_metadata
