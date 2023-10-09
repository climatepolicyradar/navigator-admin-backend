import pytest
from app.errors import RepositoryError
from app.model.analytics import SummaryDTO
import app.service.analytics as analytics_service
from sqlalchemy import exc

from unit_tests.helpers.analytics import (
    create_summary_dto,
    EXPECTED_NUM_DOCUMENTS,
    EXPECTED_NUM_FAMILIES,
    EXPECTED_NUM_COLLECTIONS,
    EXPECTED_NUM_EVENTS,
)


def expected_analytics_summary() -> SummaryDTO:
    return create_summary_dto(
        n_documents=EXPECTED_NUM_DOCUMENTS,
        n_families=EXPECTED_NUM_FAMILIES,
        n_collections=EXPECTED_NUM_COLLECTIONS,
        n_events=EXPECTED_NUM_EVENTS,
    )


# --- GET SUMMARY


def test_summary(collection_repo_mock, document_repo_mock, family_repo_mock):
    result = analytics_service.summary()
    assert result == expected_analytics_summary()

    assert result is not None
    assert result.n_events == 0

    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 1
    assert family_repo_mock.count.call_count == 1


def test_summary_returns_none(
    collection_repo_mock, document_repo_mock, family_repo_mock
):
    collection_repo_mock.return_empty = True
    result = analytics_service.summary()

    assert result is None

    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 1
    assert family_repo_mock.count.call_count == 1


def test_summary_raises_if_db_error(
    collection_repo_mock, document_repo_mock, family_repo_mock
):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError) as e:
        analytics_service.summary()

    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 0
    assert family_repo_mock.count.call_count == 0
