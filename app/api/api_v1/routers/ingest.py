import json
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from app.errors import ValidationError
from app.model.general import Json
from app.service.ingest import (
    get_collection_template,
    get_document_template,
    get_event_template,
    get_family_template,
    import_data,
    validate_ingest_data,
)

ingest_router = r = APIRouter()

_LOGGER = logging.getLogger(__name__)


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

    _LOGGER.info(f"Creating template for corpus type: {corpus_type}")

    try:
        return {
            "collections": [get_collection_template()],
            "families": [get_family_template(corpus_type)],
            "documents": [get_document_template(corpus_type)],
            "events": [get_event_template(corpus_type)],
        }
    except ValidationError as e:
        _LOGGER.error(e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)


@r.post(
    "/ingest/{corpus_import_id}",
    response_model=Json,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest(
    request: Request,
    new_data: UploadFile,
    corpus_import_id: str,
    background_tasks: BackgroundTasks,
) -> Json:
    """
    Bulk import endpoint.

    :param UploadFile new_data: file containing json representation of data to ingest.
    :return Json: json representation of the data to ingest.
    """
    _LOGGER.info(
        f"User {request.state.user} triggered bulk import for corpus: {corpus_import_id}"
    )

    try:
        content = await new_data.read()
        data_dict = json.loads(content)
        validate_ingest_data(data_dict)

        background_tasks.add_task(import_data, data_dict, corpus_import_id)

        return {
            "message": "Bulk import request accepted. Check Cloudwatch logs for result."
        }
    except ValidationError as e:
        _LOGGER.error(e.message, exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=e.message)
    except HTTPException as e:
        _LOGGER.error(e, exc_info=True)
        raise e
    except Exception as e:
        _LOGGER.error(e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
