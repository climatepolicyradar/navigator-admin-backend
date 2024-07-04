import logging

from db_client.functions import metadata

from app.errors import ValidationError

_LOGGER = logging.getLogger(__name__)


def validate_metadata(taxonomy, entity_metadata):
    """Validates the metadata against the taxonomy.

    :param _type_ taxonomy_entries: The built entries from the valid
        metadata.
    :param _type_ metadata: The metadata to validate.
    :raises ValidationError: if the metadata is invalid.
    :return None
    """
    results = metadata.validate_metadata(
        metadata.build_valid_taxonomy(taxonomy), entity_metadata
    )

    if len(results) > 0:  # type: ignore
        msg = f"Metadata validation failed: {','.join(results)}"
        _LOGGER.error(msg)
        raise ValidationError(msg)
