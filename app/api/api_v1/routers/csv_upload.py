import logging
import os

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, UploadFile, status

from app.clients.aws.s3bucket import upload_csv_to_s3
from app.model.general import Json
from app.telemetry_exceptions import ExceptionHandlingTelemetryRoute

csv_upload_router = r = APIRouter(route_class=ExceptionHandlingTelemetryRoute)


_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


@r.post("/csv-upload", response_model=Json, status_code=status.HTTP_201_CREATED)
def upload_csv(file: UploadFile) -> Json:
    """
    Upload a CSV file to S3.

    :param UploadFile file: The CSV file to upload.
    :return Json: The S3 key the file was written to.
    """
    try:
        file_name = (
            file.filename if file.filename else "untitled.csv"
        )  # To handle cases where the filename is not provided
        key = upload_csv_to_s3(file.file, file_name)
        _LOGGER.info(f"✅ CSV uploaded to {key}")
        return {"message": "CSV uploaded successfully", "key": key}
    except ClientError as e:
        _LOGGER.exception(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to upload file to S3",
        )
