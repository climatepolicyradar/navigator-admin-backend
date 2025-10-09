import json
import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, status

from app.errors import ValidationError
from app.model.general import Json
from app.service.bulk_import import (
    get_collection_template,
    get_document_template,
    get_event_template,
    get_family_template,
    import_data,
)
from app.service.validation import validate_bulk_import_data, validate_corpus_exists
from app.telemetry_exceptions import ExceptionHandlingTelemetryRoute

bulk_import_router = r = APIRouter(route_class=ExceptionHandlingTelemetryRoute)

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


@r.get(
    "/bulk-import/template/{corpus_type}",
    response_model=Json,
    status_code=status.HTTP_200_OK,
)
async def get_bulk_import_template(corpus_type: str) -> Json:
    """
    Data bulk import template endpoint.

    :param str corpus_type: type of the corpus of data to import.
    :return Json: json representation of bulk import template.
    """

    try:
        return {
            "collections": [get_collection_template(corpus_type)],
            "families": [get_family_template(corpus_type)],
            "documents": [get_document_template(corpus_type)],
            "events": [get_event_template(corpus_type)],
        }
    except ValidationError as e:
        _LOGGER.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@r.post(
    "/bulk-import/{corpus_import_id}",
    response_model=Json,
    status_code=status.HTTP_202_ACCEPTED,
)
async def bulk_import(
    data: UploadFile,
    corpus_import_id: str,
    background_tasks: BackgroundTasks,
) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile data: File containing json representation of data to import.
    :param str corpus_import_id: The ID of the corpus to import.
    :param BackgroundTasks background_tasks: Background tasks to be performed after the request is completed.
    :return Json: json representation of the data to import.
    """
    try:
        content = await data.read()
        data_dict = json.loads(content)

        _LOGGER.info("🔍 Checking that corpus exists...")
        validate_corpus_exists(corpus_import_id)

        _LOGGER.info("🔍 Validating entity relationships in data...")
        validate_bulk_import_data(data_dict)

        _LOGGER.info("✅ Validation successful")

        background_tasks.add_task(import_data, data_dict, corpus_import_id)

        return {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }
    except ValidationError as e:
        _LOGGER.exception(e.message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except HTTPException as e:
        _LOGGER.exception(e)
        raise e
    except Exception as e:
        _LOGGER.exception(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
