from typing import Optional

import pytest

import app.service.analytics as analytics_service
from app.errors import RepositoryError
from app.model.analytics import SummaryDTO
from tests.helpers.analytics import (
    EXPECTED_NUM_COLLECTIONS,
    EXPECTED_NUM_DOCUMENTS,
    EXPECTED_NUM_EVENTS,
    EXPECTED_NUM_FAMILIES,
    create_summary_dto,
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


def test_summary_superuser(
    collection_repo_mock,
    document_repo_mock,
    family_repo_mock,
    event_repo_mock,
    super_user_context,
):
    collection_repo_mock.is_superuser = True
    document_repo_mock.superuser = True
    family_repo_mock.is_superuser = True
    event_repo_mock.is_superuser = True

    result = analytics_service.summary(super_user_context)
    assert result == expected_analytics_summary()

    assert result is not None

    # Ensure the analytics service uses the other services to validate.
    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 1
    assert family_repo_mock.count.call_count == 1
    assert event_repo_mock.count.call_count == 1


def test_summary_non_superuser(
    collection_repo_mock,
    document_repo_mock,
    family_repo_mock,
    event_repo_mock,
    admin_user_context,
):
    result = analytics_service.summary(admin_user_context)
    assert result == expected_analytics_summary(
        expected_docs=11,
        expected_families=22,
        expected_collections=5,
        expected_events=2,
    )

    assert result is not None

    # Ensure the analytics service uses the other services to validate.
    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 1
    assert family_repo_mock.count.call_count == 1
    assert event_repo_mock.count.call_count == 1


def test_summary_returns_none(
    collection_repo_mock,
    document_repo_mock,
    family_repo_mock,
    event_repo_mock,
    admin_user_context,
):
    collection_repo_mock.return_empty = True
    result = analytics_service.summary(admin_user_context)
    assert result == expected_analytics_summary(
        expected_docs=11,
        expected_families=22,
        expected_collections=None,
        expected_events=2,
    )

    # Ensure the analytics service uses the other services to validate.
    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 1
    assert family_repo_mock.count.call_count == 1
    assert event_repo_mock.count.call_count == 1


def test_summary_raises_if_db_error(
    collection_repo_mock,
    document_repo_mock,
    family_repo_mock,
    event_repo_mock,
    admin_user_context,
):
    collection_repo_mock.throw_repository_error = True
    with pytest.raises(RepositoryError):
        analytics_service.summary(admin_user_context)

    # Ensure the analytics service uses the other services to validate.
    assert collection_repo_mock.count.call_count == 1
    assert document_repo_mock.count.call_count == 0
    assert family_repo_mock.count.call_count == 0
    assert event_repo_mock.count.call_count == 0
