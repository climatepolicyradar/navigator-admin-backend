from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.clients.db.models.law_policy.family import (
    DocumentStatus,
)


class DocumentReadDTO(BaseModel):
    """Representation of a Document."""

    # From FamilyDocument
    import_id: str
    family_import_id: str
    variant_name: Optional[str]
    status: DocumentStatus
    role: Optional[str]
    type: Optional[str]
    slug: str
    created: datetime
    last_modified: datetime
    # From PhysicalDocument
    physical_id: int
    title: str
    md5_sum: Optional[str]
    cdn_object: Optional[str]
    source_url: Optional[str]
    content_type: Optional[str]
    user_language_name: Optional[str]
    calc_language_name: Optional[str]


class DocumentWriteDTO(BaseModel):
    """Representation of a Document."""

    # From FamilyDocument
    variant_name: Optional[str]
    role: Optional[str]
    type: Optional[str]
    title: str
    source_url: Optional[str]
    user_language_name: Optional[str]


class DocumentCreateDTO(BaseModel):
    """Representation of a Document."""

    # From FamilyDocument
    family_import_id: str
    variant_name: Optional[str] = None
    role: str
    type: Optional[str] = None

    # From PhysicalDocument
    title: str
    source_url: str
    user_language_name: Optional[str]


class DocumentUploadRequest(BaseModel):
    """Request for a document upload"""

    filename: str
    overwrite: Optional[bool] = False


class DocumentUploadResponse(BaseModel):
    """Details required to upload a document"""

    presigned_upload_url: str
    cdn_url: str
