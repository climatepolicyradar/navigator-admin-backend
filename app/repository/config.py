import logging
from typing import Any
from sqlalchemy.orm import Session
from app.clients.db.models.app.users import Organisation
from app.clients.db.models.document.physical_document import Language
from app.clients.db.models.law_policy.geography import Geography
from app.clients.db.models.law_policy.metadata import (
    MetadataOrganisation,
    MetadataTaxonomy,
)
from app.clients.db.session import AnyModel
from app.model.config import ConfigReadDTO, TaxonomyData


_LOGGER = logging.getLogger(__name__)


def _tree_table_to_json(
    table: AnyModel,
    db: Session,
) -> list[dict]:
    json_out = []
    child_list_map: dict[int, Any] = {}

    for row in db.query(table).order_by(table.id).all():
        row_object = {col.name: getattr(row, col.name) for col in row.__table__.columns}
        row_children: list[dict[str, Any]] = []
        child_list_map[row_object["id"]] = row_children

        # No parent indicates a top level element
        node_row_object = {"node": row_object, "children": row_children}
        node_id = row_object["parent_id"]
        if node_id is None:
            json_out.append(node_row_object)
        else:
            append_list = child_list_map.get(node_id)
            if append_list is None:
                raise RuntimeError(f"Could not locate parent node with id {node_id}")
            append_list.append(node_row_object)

    return json_out


def _get_organisation_taxonomy_by_name(db: Session, org_name: str) -> TaxonomyData:
    """
    Returns the TaxonomyConfig for the named organisation

    :param Session db: connection to the database
    :return TaxonomyConfig: the TaxonomyConfig from the db
    """
    return (
        db.query(MetadataTaxonomy.valid_metadata)
        .join(
            MetadataOrganisation,
            MetadataOrganisation.taxonomy_id == MetadataTaxonomy.id,
        )
        .join(Organisation, Organisation.id == MetadataOrganisation.organisation_id)
        .filter_by(name=org_name)
        .one()[0]
    )


def get(db: Session) -> ConfigReadDTO:
    """
    Returns the configuration for the admin service.

    :param Session db: connection to the database
    :return ConfigReadDTO: The config data
    """

    # TODO: Return the event types too
    geographies = _tree_table_to_json(table=Geography, db=db)
    taxonomies = {
        org.name: _get_organisation_taxonomy_by_name(db=db, org_name=org.name)
        for org in db.query(Organisation).all()
    }
    languages = {lang.language_code: lang.name for lang in db.query(Language).all()}
    return ConfigReadDTO(
        geographies=geographies, taxonomies=taxonomies, languages=languages
    )
