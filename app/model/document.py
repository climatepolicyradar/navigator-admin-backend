from typing import Optional
from pydantic import BaseModel


class DocumentDTO(BaseModel):
    """Representation of a Document."""

    import_id: str


class DocumentUploadRequest(BaseModel):
    """Request for a document upload"""

    filename: str
    overwrite: Optional[bool] = False


class DocumentUploadResponse(BaseModel):
    """Details required to upload a document"""

    presigned_upload_url: str
    cdn_url: str
