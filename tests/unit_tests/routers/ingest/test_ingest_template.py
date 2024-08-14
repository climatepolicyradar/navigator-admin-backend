"""
Tests the route for retrieving a data ingest template by corpus.

This uses service mocks and ensures the endpoint calls into each service.
"""

from fastapi import status
from fastapi.testclient import TestClient


def test_ingest_template_when_not_authenticated(client: TestClient):
    response = client.get(
        "/api/v1/ingest/template/test_corpus_type",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_ingest_template_when_ok(client: TestClient, user_header_token):

    response = client.get(
        "/api/v1/ingest/template/test_corpus_type",
        headers=user_header_token,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "collections": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "title": {"title": "Title", "type": "string"},
                "description": {"title": "Description", "type": "string"},
            }
        ],
        "families": [
            {
                "import_id": {"title": "Import Id", "type": "string"},
                "title": {"title": "Title", "type": "string"},
                "summary": {"title": "Summary", "type": "string"},
                "geography": {"title": "Geography", "type": "string"},
                "category": {"title": "Category", "type": "string"},
                "metadata": {
                    "author": {
                        "allow_any": "true",
                        "allow_blanks": "false",
                        "allowed_values": [],
                    },
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
                },
                "collections": {
                    "items": {"type": "string"},
                    "title": "Collections",
                    "type": "array",
                },
                "events": [
                    {
                        "event_title": {"title": "Event Title", "type": "string"},
                        "date": {
                            "format": "date-time",
                            "title": "Date",
                            "type": "string",
                        },
                        "event_type_value": {
                            "title": "Event Type Value",
                            "type": "string",
                        },
                    }
                ],
                "documents": [
                    {
                        "events": [
                            {
                                "event_title": {
                                    "title": "Event Title",
                                    "type": "string",
                                },
                                "date": {
                                    "format": "date-time",
                                    "title": "Date",
                                    "type": "string",
                                },
                                "event_type_value": {
                                    "title": "Event Type Value",
                                    "type": "string",
                                },
                            }
                        ],
                        "variant_name": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "default": None,
                            "title": "Variant Name",
                        },
                        "metadata": {
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
                        "title": {"title": "Title", "type": "string"},
                        "source_url": {
                            "anyOf": [
                                {"format": "uri", "minLength": 1, "type": "string"},
                                {"type": "null"},
                            ],
                            "default": None,
                            "title": "Source Url",
                        },
                        "user_language_name": {
                            "anyOf": [{"type": "string"}, {"type": "null"}],
                            "title": "User Language Name",
                        },
                    }
                ],
            }
        ],
    }
