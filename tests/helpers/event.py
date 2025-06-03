from datetime import datetime, timezone

from db_client.models.dfce.family import EventStatus

from app.model.event import EventCreateDTO, EventMetadata, EventReadDTO, EventWriteDTO


def create_event_read_dto(
    import_id: str, family_import_id: str = "test.family.1.0", title: str = "title"
) -> EventReadDTO:
    return EventReadDTO(
        import_id=import_id,
        event_title=title,
        date=datetime.strptime("2020-01-01", "%Y-%m-%d"),
        event_type_value="Amended",
        family_import_id=family_import_id,
        family_document_import_id=None,
        event_status=EventStatus.OK,
        created=datetime.now(),
        last_modified=datetime.now(),
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
        metadata=EventMetadata(
            event_type=["Passed/Approved"],
            datetime_event_name=["Passed/Approved"],
        ),
    )


def create_event_write_dto(
    title: str = "title",
    event_type_value: str = "Amended",
    datetime_event_name: str = "Passed/Approved",
    date: datetime = datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
) -> EventWriteDTO:
    return EventWriteDTO(
        event_title=title,
        date=date,
        event_type_value=event_type_value,
        metadata=EventMetadata(
            event_type=[event_type_value],
            datetime_event_name=[datetime_event_name],
        ),
    )
