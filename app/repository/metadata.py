from typing import Optional

from db_client.models.organisation import Corpus, CorpusType
from sqlalchemy.orm import Session

from app.model.general import Json


def get_schema_for_corpus(db: Session, corpus_import_id: str) -> Optional[Json]:
    """Gets the schema for an organisation.

    :param Session db: The DB session to query.
    :param str corpus_import_id: The import ID of the corpus to get the
        schema for.
    :return: None or a JSON object containing the valid metadata for the
        given corpus.
    """
    corpus_type = (
        db.query(CorpusType)
        .join(
            Corpus,
            Corpus.corpus_type_name == CorpusType.name,
        )
        .filter(Corpus.import_id == corpus_import_id)
        .one_or_none()
    )
    if corpus_type is not None:
        return corpus_type.valid_metadata
