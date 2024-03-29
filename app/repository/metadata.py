from typing import Optional

from db_client.models.dfce.metadata import MetadataOrganisation, MetadataTaxonomy
from sqlalchemy.orm import Session

from app.model.general import Json


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
