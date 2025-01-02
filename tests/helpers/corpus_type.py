from typing import Optional

from app.model.corpus_type import CorpusTypeCreateDTO


def create_corpus_type_create_dto(
    name: str = "test_name",
    description: str = "test_description",
    metadata: Optional[dict] = None,
) -> CorpusTypeCreateDTO:
    if metadata is None:
        metadata = {
            "event_type": ["Passed/Approved"],
            "_event": {
                "event_type": ["Passed/Approved"],
                "datetime_event_name": ["Passed/Approved"],
            },
            "_document": {},
        }

    return CorpusTypeCreateDTO(
        name=name,
        description=description,
        metadata=metadata,
    )
