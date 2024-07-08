import logging
from typing import Optional, Sequence, cast

from db_client.functions import metadata as metadata_repo
from db_client.functions.corpus_helpers import TaxonomyDataEntry
from sqlalchemy.orm import Session

from app.errors import ValidationError

_LOGGER = logging.getLogger(__name__)


def validate_metadata(
    db: Session,
    corpus_id: str,
    metadata: TaxonomyDataEntry,
    entity_key: Optional[str] = None,
) -> Optional[Sequence[str]]:
    """Validates the metadata against the taxonomy.

    :param Session db: The session to query against.
    :param str corpus_id: The corpus ID to get the taxonomy for.
    :param TaxonomyDataEntry metadata: The metadata to validate.
    :param Optional[str] entity_key: The entity specific taxonomy key if
        exists, otherwise None (which represents validating Family
        metadata).
    :raises ValidationError: if the metadata is invalid.
    :return None
    """
    results = metadata_repo.validate_metadata(db, corpus_id, metadata, entity_key)

    if results is not None and len(results) > 0:  # type: ignore
        msg = f"Metadata validation failed: {','.join(cast(list, results))}"
        _LOGGER.error(msg)
        raise ValidationError(msg)
