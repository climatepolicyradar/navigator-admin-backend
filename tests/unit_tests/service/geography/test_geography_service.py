import pytest

import app.service.geography as geography_service
from app.errors import ValidationError


def test_geo_service_validate_raises_when_invalid(
    organisation_repo_mock,
    geography_repo_mock,
):
    geography_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        result = geography_service.get_id(None, "CHN")  # type: ignore
        assert result is None

    expected_msg = "The geography value CHN is invalid!"
    assert e.value.message == expected_msg
    assert geography_repo_mock.get_id_from_value.call_count == 1


def test_geo_service_raises_error_when_validating_invalid_geo_ids(
    geography_repo_mock,
):
    geography_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        result = geography_service.get_ids(None, ["CHN", "USA", "AGO"])  # type: ignore
        assert result == []

    expected_msg = (
        "One or more of the following geography values are invalid: CHN, USA, AGO"
    )
    assert e.value.message == expected_msg
    assert geography_repo_mock.get_ids_from_values.call_count == 1


def test_geo_service_gets_ids_from_repo(
    geography_repo_mock,
):
    result = geography_service.get_ids(None, ["CHN", "USA"])  # type: ignore
    assert result == [1, 2]
    assert geography_repo_mock.get_ids_from_values.call_count == 1
