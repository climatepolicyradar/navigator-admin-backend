from pytest import MonkeyPatch

from app.errors import RepositoryError
from app.model.analytics import SummaryDTO
from unit_tests.helpers.analytics import create_summary_dto


def mock_analytics_service(analytics_service, monkeypatch: MonkeyPatch, mocker):
    analytics_service.return_empty = False
    analytics_service.throw_repository_error = False

    def maybe_throw():
        if analytics_service.throw_repository_error:
            raise RepositoryError("bad repo")

    def mock_get_summary() -> SummaryDTO:
        maybe_throw()
        if analytics_service.return_empty is True:
            return create_summary_dto(
                n_documents=33,
                n_families=22,
                n_collections=None,
                n_events=5,
            )

        return create_summary_dto(
            n_documents=33,
            n_families=22,
            n_collections=11,
            n_events=5,
        )

    monkeypatch.setattr(analytics_service, "summary", mock_get_summary)
    mocker.spy(analytics_service, "summary")
