import logging
from typing import Any

from fastapi import APIRouter, UploadFile, status

from app.model.collection import CollectionCreateDTO
from app.model.document import DocumentCreateDTO
from app.model.event import EventCreateDTO
from app.model.family import FamilyCreateDTO
from app.model.general import Json

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


def get_collection_template():
    collection_schema = CollectionCreateDTO.model_json_schema(mode="serialization")
    collection_template = collection_schema["properties"]

    return collection_template


def get_event_template():
    event_schema = EventCreateDTO.model_json_schema(mode="serialization")
    event_template = event_schema["properties"]

    del event_template["family_import_id"]
    del event_template["family_document_import_id"]

    return event_template


def get_document_template(event_template: Any):
    document_schema = DocumentCreateDTO.model_json_schema(mode="serialization")
    document_template = document_schema["properties"]

    del document_template["family_import_id"]
    document_template["events"] = [event_template]

    return document_template


def get_metadata_template(corpus_type: str):
    # hardcoding UNFCC taxonomy for the moment
    # will need to look up valid_metadata in the corpus_type table where name == corpus_type
    return {
        "author": {"allow_any": "true", "allow_blanks": "false", "allowed_values": []},
        "author_type": {
            "allow_any": "false",
            "allow_blanks": "false",
            "allowed_values": ["Party", "Non-Party"],
        },
        "event_type": {
            "allow_any": "false",
            "allow_blanks": "true",
            "allowed_values": [
                "Amended",
                "Appealed",
                "Closed",
                "Declaration Of Climate Emergency",
                "Dismissed",
                "Entered Into Force",
                "Filing",
                "Granted",
                "Implementation Details",
                "International Agreement",
                "Net Zero Pledge",
                "Other",
                "Passed/Approved",
                "Repealed/Replaced",
                "Set",
                "Settled",
                "Updated",
            ],
        },
        "_document": {
            "role": {
                "allow_any": "false",
                "allow_blanks": "false",
                "allowed_values": [
                    "MAIN",
                    "AMENDMENT",
                    "SUPPORTING LEGISLATION",
                    "SUMMARY",
                    "PREVIOUS VERSION",
                    "ANNEX",
                    "SUPPORTING DOCUMENTATION",
                    "INFORMATION WEBPAGE",
                    "PRESS RELEASE",
                    "DOCUMENT(S) STORED ON WEBPAGE",
                ],
            },
            "type": {
                "allow_any": "false",
                "allow_blanks": "false",
                "allowed_values": [
                    "Accord",
                    "Act",
                    "Action Plan",
                    "Agenda",
                    "Annex",
                    "Assessment",
                    "Bill",
                    "Constitution",
                    "Criteria",
                    "Decision",
                    "Decision and Plan",
                    "Decree",
                    "Decree Law",
                    "Directive",
                    "Discussion Paper",
                    "Edict",
                    "EU Decision",
                    "EU Directive",
                    "EU Regulation",
                    "Executive Order",
                    "Framework",
                    "Law",
                    "Law and Plan",
                    "Order",
                    "Ordinance",
                    "Plan",
                    "Policy",
                    "Press Release",
                    "Programme",
                    "Protocol",
                    "Roadmap",
                    "Regulation",
                    "Resolution",
                    "Royal Decree",
                    "Rules",
                    "Statement",
                    "Strategic Assessment",
                    "Strategy",
                    "Summary",
                    "Vision",
                    "Biennial Report",
                    "Biennial Update Report",
                    "Facilitative Sharing of Views Report",
                    "Global Stocktake Synthesis Report",
                    "Industry Report",
                    "Intersessional Document",
                    "Long-Term Low-Emission Development Strategy",
                    "National Communication",
                    "National Inventory Report",
                    "Pre-Session Document",
                    "Progress Report",
                    "Publication",
                    "Report",
                    "Submission to the Global Stocktake",
                    "Summary Report",
                    "Synthesis Report",
                    "Technical Analysis Summary Report",
                    "Nationally Determined Contribution",
                    "Adaptation Communication",
                    "National Adaptation Plan",
                    "Technology Needs Assessment",
                    "Fast-Start Finance Report",
                    "IPCC Report",
                    "Annual Compilation and Accounting Report",
                    "Biennial Report,National Communication",
                    "Biennial Update Report,National Communication",
                    "National Adaptation Plan,Adaptation Communication",
                    "National Communication,Biennial Report",
                    "National Communication,Biennial Update Report",
                    "Nationally Determined Contribution,Adaptation Communication",
                    "Nationally Determined Contribution,National Communication",
                    "Pre-Session Document,Annual Compilation and Accounting Report",
                    "Pre-Session Document,Progress Report",
                    "Pre-Session Document,Synthesis Report",
                    "Publication,Report",
                    "Technical Analysis Technical Report",
                ],
            },
        },
    }


def get_family_template(corpus_type: str):
    family_schema = FamilyCreateDTO.model_json_schema(mode="serialization")
    family_template = family_schema["properties"]

    del family_template["corpus_import_id"]

    # look up taxonomy by corpus type
    family_metadata = get_metadata_template(corpus_type)
    # pull out document taxonomy
    document_metadata = family_metadata.pop("_document")

    # add family metadata and event templates to the family template
    family_template["metadata"] = family_metadata
    event_template = get_event_template()
    family_template["events"] = [event_template]

    # get document template
    document_template = get_document_template(event_template)
    # add document metadata template
    document_template["metadata"] = document_metadata
    # add document template to the family template
    family_template["documents"] = [document_template]

    return family_template


@r.get(
    "/ingest/template/{corpus_type}",
    response_model=Json,
    status_code=status.HTTP_200_OK,
)
async def get_ingest_template(corpus_type: str) -> Json:
    """
    Data ingest template endpoint.

    :param str corpus_type: type of the corpus of data to ingest.
    :return Json: json representation of ingest template.
    """

    _LOGGER.info(corpus_type)

    return {
        "collections": [get_collection_template()],
        "families": [get_family_template(corpus_type)],
    }


@r.post("/ingest", response_model=Json, status_code=status.HTTP_201_CREATED)
async def ingest_data(new_data: UploadFile) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """
    _LOGGER.info(new_data)
    return {"hello": "world"}
