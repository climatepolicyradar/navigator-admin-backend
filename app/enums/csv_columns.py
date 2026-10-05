from enum import StrEnum


class CSVColumn(StrEnum):
    """
    Columns required in an uploaded CSV.

    ORDER MATTERS: members are validated in the order they are defined here,
    which must match the order shown on the upload page.
    """

    DOCUMENT_ID = "document_id"
    DOCUMENT_TITLE = "document_title"
    ALTERNATIVE_TITLES = "alternative_titles"
    DOCUMENT_FUNCTION = "document_function"
    SUMMARY = "summary"
    REFERENCE_NUMBER = "reference_number"
    ENTITY_TYPE = "entity_type"
    EVENT_TYPE = "event_type"
    EVENT_DATE = "event_date"
    EVENT_DESCRIPTION = "event_description"
    REGION = "region"
    REGION_CODE = "region_code"
    GEOGRAPHY = "geography"
    GEOGRAPHY_CODE = "geography_code"
    SUBDIVISION = "subdivision"
    SUBDIVISION_CODE = "subdivision_code"
    DOMAIN = "domain"
    RESPONSE_AREAS = "response_areas"
    DATA_PROVIDER = "data_provider"
    ACCREDITATION_TEXT = "accreditation_text"
    ATTRIBUTION_URL = "attribution_url"
    ACCREDITATION_LOGO = "accreditation_logo"
    SOURCE_URL = "source_url"
    DOCUMENT_TYPE = "document_type"
    TYPE = "type"
    VARIANT = "variant"
    LANGUAGE = "language"
    LANGUAGE_CODE = "language_code"
    PARENT_DOCUMENT_ID = "parent_document_id"
