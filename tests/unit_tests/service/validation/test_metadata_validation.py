import pytest

from app.errors import ValidationError
from app.service.validation import validate_metadata_values_are_strings


def test_validate_metadata_when_ok():
    test_data = {
        "entity1": [{"metadata": {"key1": ["value"], "key2": [""]}}],
        "entity2": [{"other_key": {"key1": ["value"]}}],
        "entity3": [{}],
        "entity4": [],
        "entity5": "",
        "entity6": None,
    }

    validate_metadata_values_are_strings(test_data)


@pytest.mark.parametrize(
    "test_data",
    [
        {"entity": [{"metadata": {"key": [1]}}]},
        {"entity": [{"metadata": {"key": [1]}}]},
        {"entity": [{"metadata": {"key": 1}}]},
        {"entity": [{"metadata": {"key": [None]}}]},
        {"entity": [{"metadata": {"key": None}}]},
    ],
)
def test_validate_metadata_throws_exception_when_non_string_values_present(test_data):

    with pytest.raises(ValidationError) as e:
        validate_metadata_values_are_strings(test_data)
    assert "Metadata values should be strings" == e.value.message
