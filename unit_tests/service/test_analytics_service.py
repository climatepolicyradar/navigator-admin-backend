from typing import Optional

import pytest

from db_client.errors import RepositoryError
from app.model.analytics import SummaryDTO
import app.service.analytics as analytics_service

from unit_tests.helpers.analytics import (
    create_summary_dto,
    EXPECTED_NUM_DOCUMENTS,
    EXPECTED_NUM_FAMILIES,
    EXPECTED_NUM_COLLECTIONS,
    EXPECTED_NUM_EVENTS,
)


def expected_analytics_summary(
    expected_docs: Optional[int] = EXPECTED_NUM_DOCUMENTS,
    expected_families: Optional[int] = EXPECTED_NUM_FAMILIES,
    expected_collections: Optional[int] = EXPECTED_NUM_COLLECTIONS,
    expected_events: Optional[int] = EXPECTED_NUM_EVENTS,
) -> SummaryDTO:
    return create_summary_dto(
        n_documents=expected_docs,
        n_families=expected_families,
        n_collections=expected_collections,
        n_events=expected_events,
    )


# --- GET SUMMARY


def test_summary(
    collection_repo_mock, document_repo_mock, family_repo_mock, event_repo_mock
):
    result = analytics_service.summary()
    assert result == expected_analytics_summary()

    assert result is not None

    # Ensure the analytics service uses the other services to validate.
    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 1
    assert family_repo_mock.count.call_count == 1
    assert event_repo_mock.count.call_count == 1


def test_summary_returns_none(
    collection_repo_mock, document_repo_mock, family_repo_mock, event_repo_mock
):
    collection_repo_mock.return_empty = True
    result = analytics_service.summary()
    assert result == expected_analytics_summary(expected_collections=None)

    # Ensure the analytics service uses the other services to validate.
    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 1
    assert family_repo_mock.count.call_count == 1
    assert event_repo_mock.count.call_count == 1


def test_summary_raises_if_db_error(
    collection_repo_mock, document_repo_mock, family_repo_mock, event_repo_mock
):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        analytics_service.summary()

    # Ensure the analytics service uses the other services to validate.
    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 0
    assert family_repo_mock.count.call_count == 0
    assert event_repo_mock.count.call_count == 0
