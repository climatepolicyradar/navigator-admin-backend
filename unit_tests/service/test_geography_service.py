import pytest
from app.errors.validation_error import ValidationError
import app.service.geography as geography_service
from unit_tests.mocks.geography_repo import INVALID_GEO_VALUE


def test_geo_service_validate_raiseson_invalid_value(geography_repo_mock):
    with pytest.raises(ValidationError) as e:
        result = geography_service.validate(None, INVALID_GEO_VALUE)  # type: ignore
        assert result is None

    expected_msg = f"The geography value {INVALID_GEO_VALUE} is invalid!"
    assert e.value.message == expected_msg
    assert geography_repo_mock.get_id_from_value.call_count == 1
