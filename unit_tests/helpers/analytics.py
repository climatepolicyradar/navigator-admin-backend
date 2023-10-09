from app.model.analytics import SummaryDTO

# ANALYTICS SUMMARY
EXPECTED_NUM_DOCUMENTS = 33
EXPECTED_NUM_FAMILIES = 22
EXPECTED_NUM_COLLECTIONS = 11
EXPECTED_NUM_EVENTS = 0


def create_summary_dto(
    n_documents: int, n_families: int, n_collections: int, n_events: int = 0
) -> SummaryDTO:
    return SummaryDTO(
        n_documents=n_documents,
        n_families=n_families,
        n_collections=n_collections,
        n_events=n_events,
    )
