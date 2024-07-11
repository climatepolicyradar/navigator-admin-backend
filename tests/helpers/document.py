from datetime import datetime
from typing import Optional, Union, cast

from db_client.models.dfce.family import DocumentStatus
from pydantic import AnyHttpUrl

from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
from app.model.general import Json


def create_document_create_dto(
    family_import_id="test.family.1.0",
    title: str = "title",
    variant_name: Optional[str] = "Original Language",
    source_url: Optional[Union[str, AnyHttpUrl]] = "http://source",
    user_language_name: Optional[str] = None,
    metadata: Optional[Json] = None,
) -> DocumentCreateDTO:
    if source_url is not None:
        source_url = cast(AnyHttpUrl, source_url)
    if metadata is None:
        metadata = {"role": ["MAIN"], "type": ["Law"]}
    return DocumentCreateDTO(
        family_import_id=family_import_id,
        variant_name=variant_name,
        type="Law",
        metadata=metadata,
        title=title,
        source_url=source_url,
        user_language_name=user_language_name,
    )


def create_document_write_dto(
    title: str = "title",
    variant_name: Optional[str] = "Original Language",
    metadata: Optional[Json] = None,
    source_url: Optional[str] = "http://update_source",
    user_language_name: Optional[str] = "English",
) -> DocumentWriteDTO:

    if metadata is None:
        metadata = {"role": ["MAIN"], "type": ["Law"]}
    return DocumentWriteDTO(
        variant_name=variant_name,
        type="Law",
        metadata=metadata,
        title=title,
        source_url=(
            cast(AnyHttpUrl, "http://update_source")
            if isinstance(source_url, str)
            else None
        ),
        user_language_name=user_language_name,
    )


def create_document_read_dto(
    import_id: str,
    family_import_id="test.family.1.0",
    title: str = "title",
    variant_name: Optional[str] = "Original Language",
    metadata: Optional[Json] = None,
) -> DocumentReadDTO:
    if metadata is None:
        metadata = {"role": ["MAIN"], "type": ["Law"]}
    return DocumentReadDTO(
        import_id=import_id,
        family_import_id=family_import_id,
        variant_name=variant_name,
        status=DocumentStatus.CREATED,
        type="Law",
        metadata=metadata,
        slug="",
        physical_id=1,
        title=title,
        md5_sum="sum",
        cdn_object="cdn",
        source_url=cast(AnyHttpUrl, "http://source"),
        content_type="content_type",
        user_language_name="Ghotuo",
        calc_language_name=None,
        created=datetime.now(),
        last_modified=datetime.now(),
    )
