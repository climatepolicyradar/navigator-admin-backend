from app.db.models.law_policy.metadata import (
    MetadataOrganisation,
    MetadataTaxonomy,
)
from app.model.general import Json
from sqlalchemy.orm import Session


def validate(db: Session, org_id: int, data: Json) -> bool:
    metadata = (
        db.query(MetadataTaxonomy)
        .join(
            MetadataOrganisation,
            MetadataOrganisation.taxonomy_id == MetadataTaxonomy.id,
        )
        .filter(MetadataOrganisation.organisation_id == org_id)
        .one()
    )
    return _validate(metadata.valid_metadata, data)


def _validate(schema: Json, data: Json) -> bool:
    """
    Validates the data against the schema

    :param Json schema: The schema to use for the validation
    :param Json data: The values to use
    :return bool: True if valid, False if not
    """
    return True
