from app.clients.db.models.law_policy.family import EventStatus
from app.model.event import EventCreateDTO, EventReadDTO

from datetime import datetime, timezone


def create_event_read_dto(
    import_id: str, family_import_id: str = "test.family.1.0", title: str = "title"
) -> EventReadDTO:
    return EventReadDTO(
        import_id=import_id,
        event_title=title,
        date=datetime.now(timezone.utc),
        event_type_value="Amended",
        family_import_id=family_import_id,
        family_document_import_id=None,
        event_status=EventStatus.OK,
    )


def create_event_create_dto(
    family_import_id: str = "test.family.1.0", title: str = "title"
) -> EventCreateDTO:
    return EventCreateDTO(
        event_title=title,
        date=datetime.now(timezone.utc),
        event_type_value="Passed/Approved",
        family_import_id=family_import_id,
        family_document_import_id=None,
        event_status=EventStatus.OK,
    )