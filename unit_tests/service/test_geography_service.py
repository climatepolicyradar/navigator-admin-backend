import pytest
from app.errors import ValidationError
import app.service.geography as geography_service


def test_geo_service_validate_raiseson_invalid_value(
    organisation_repo_mock,
    geography_repo_mock,
):
    geography_repo_mock.error = True
    with pytest.raises(ValidationError) as e:
        result = geography_service.validate(None, "CHN")  # type: ignore
        assert result is None

    expected_msg = "The geography value CHN is invalid!"
    assert e.value.message == expected_msg
    assert geography_repo_mock.get_id_from_value.call_count == 1
