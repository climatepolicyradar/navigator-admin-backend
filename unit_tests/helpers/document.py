from app.clients.db.models.law_policy.family import DocumentStatus
from app.model.document import DocumentReadDTO


def create_document_dto(
    import_id: str, family_import_id="test.family.1.0", title: str = "title"
) -> DocumentReadDTO:
    return DocumentReadDTO(
        import_id=import_id,
        family_import_id=family_import_id,
        variant_name="Original language",
        status=DocumentStatus.CREATED,
        role="role",
        type="type",
        slug="slug",
        physical_id=1, 
        title=title,
        md5_sum="md5",
        cdn_object="cdn",
        source_url="source",
        content_type="content",
        user_language_name="lang"
    )
