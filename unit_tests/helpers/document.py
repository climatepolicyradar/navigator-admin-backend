from datetime import datetime
from typing import Optional

from app.clients.db.models.law_policy.family import DocumentStatus
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO


def create_document_create_dto(
    family_import_id="test.family.1.0",
    title: str = "title",
    variant_name: Optional[str] = "Original Language",
    user_language_name: Optional[str] = None,
) -> DocumentCreateDTO:
    return DocumentCreateDTO(
        family_import_id=family_import_id,
        variant_name=variant_name,
        role="MAIN",
        type="Law",
        title=title,
        source_url="source",
        user_language_name=user_language_name,
    )


def create_document_write_dto(
    title: str = "title",
    variant_name: Optional[str] = "Original Language",
) -> DocumentWriteDTO:
    return DocumentWriteDTO(
        variant_name=variant_name,
        role="MAIN",
        type="Law",
        title=title,
        source_url="source",
        user_language_name="Ghotuo",
    )


def create_document_read_dto(
    import_id: str,
    family_import_id="test.family.1.0",
    title: str = "title",
    variant_name: Optional[str] = "Original Language",
) -> DocumentReadDTO:
    return DocumentReadDTO(
        import_id=import_id,
        family_import_id=family_import_id,
        variant_name=variant_name,
        status=DocumentStatus.CREATED,
        role="MAIN",
        type="Law",
        slug="",
        physical_id=1,
        title=title,
        md5_sum="sum",
        cdn_object="cdn",
        source_url="source",
        content_type="content_type",
        user_language_name="Ghotuo",
        calc_language_name=None,
        created=datetime.now(),
        last_modified=datetime.now(),
    )
