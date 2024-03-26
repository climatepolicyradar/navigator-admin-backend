from typing import Optional

from app.model.analytics import SummaryDTO

# ANALYTICS SUMMARY
EXPECTED_NUM_DOCUMENTS = 33
EXPECTED_NUM_FAMILIES = 22
EXPECTED_NUM_COLLECTIONS = 11
EXPECTED_NUM_EVENTS = 5


def create_summary_dto(
    n_documents: Optional[int],
    n_families: Optional[int],
    n_collections: Optional[int],
    n_events: Optional[int],
) -> SummaryDTO:
    return SummaryDTO(
        n_documents=n_documents,
        n_families=n_families,
        n_collections=n_collections,
        n_events=n_events,
    )
