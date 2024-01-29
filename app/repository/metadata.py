from typing import Optional
from db_client.models.law_policy.metadata import (
    MetadataOrganisation,
    MetadataTaxonomy,
)
from app.model.general import Json
from sqlalchemy.orm import Session


def get_schema_for_org(db: Session, org_id: int) -> Optional[Json]:
    metadata = (
        db.query(MetadataTaxonomy)
        .join(
            MetadataOrganisation,
            MetadataOrganisation.taxonomy_id == MetadataTaxonomy.id,
        )
        .filter(MetadataOrganisation.organisation_id == org_id)
        .one_or_none()
    )
    if metadata is not None:
        return metadata.valid_metadata
