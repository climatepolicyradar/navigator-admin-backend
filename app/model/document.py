from typing import Optional
from pydantic import BaseModel

from app.clients.db.models.law_policy.family import (
    DocumentStatus,
    FamilyDocumentRole,
    FamilyDocumentType,
    Variant,
)


class DocumentDTO(BaseModel):
    """Representation of a Document."""

    # From FamilyDocument
    import_id: str
    family_import_id: str
    variant_name: Variant
    status: DocumentStatus
    role: FamilyDocumentRole
    type: FamilyDocumentType
    slug: str
    # From PhysicalDocument
    physical_id: int
    title: str
    md5_sum: str
    cdn_object: str
    source_url: str
    content_type: str
    user_language_name: str
    # TODO: Languages for a document
    # languages: list[]


class DocumentUploadRequest(BaseModel):
    """Request for a document upload"""

    filename: str
    overwrite: Optional[bool] = False


class DocumentUploadResponse(BaseModel):
    """Details required to upload a document"""

    presigned_upload_url: str
    cdn_url: str
