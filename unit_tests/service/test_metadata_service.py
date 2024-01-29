import json

import pytest
from db_client.errors import ValidationError
from app.service.metadata import _validate


SCHEMA_VALUES_NO_BLANKS = json.loads(
    """
{
  "author": {
    "allow_blanks": false,
    "allowed_values": ["peter", "joel", "mark"]
  }
}
"""
)

SCHEMA_VALUES_BLANKS = json.loads(
    """
{
  "author": {
    "allow_blanks": true,
    "allowed_values": ["peter", "joel", "mark"]
  }
}
"""
)

SCHEMA_ANY_NO_BLANKS = json.loads(
    """
{
  "author": {
    "allow_any": true,
    "allow_blanks": false,
    "allowed_values": []
  }
}
"""
)

SCHEMA_ANY_BLANKS = json.loads(
    """
{
  "author": {
    "allow_any": true,
    "allow_blanks": true,
    "allowed_values": []
  }
}
"""
)


# ----- PASSES


def test_good_when_any_and_allow_blanks():
    assert _validate(SCHEMA_ANY_BLANKS, {"author": ["henry"]})
    assert _validate(SCHEMA_ANY_BLANKS, {"author": ""})


def test_good_when_values_and_allow_blanks():
    assert _validate(SCHEMA_VALUES_BLANKS, {"author": ["peter"]})
    assert _validate(SCHEMA_VALUES_BLANKS, {"author": ""})


def test_good_when_any_and_no_blanks():
    assert _validate(SCHEMA_ANY_NO_BLANKS, {"author": ["henry"]})


def test_good_when_values_and_no_blanks():
    assert _validate(SCHEMA_VALUES_NO_BLANKS, {"author": ["peter"]})


def test_good_when_blank_schema_and_data():
    assert _validate({}, {})


# ----- FAILS


def test_fails_when_no_data():
    with pytest.raises(ValidationError) as e:
        _validate(SCHEMA_ANY_BLANKS, {})
    expected_msg = "Values for the following are missing: {'author'}"
    assert e.value.message == expected_msg


def test_fails_when_invalid_key():
    with pytest.raises(ValidationError) as e:
        _validate(SCHEMA_ANY_BLANKS, {"Something": ["value"], "author": ["peter"]})
    expected_msg = "Unknown 'Something' not in ['author']"
    assert e.value.message == expected_msg


def test_fails_when_any_and_allow_blanks():
    # This should never fail
    pass


def test_fails_when_values_and_allow_blanks():
    with pytest.raises(ValidationError) as e:
        _validate(SCHEMA_VALUES_BLANKS, {"author": ["henry"]})
    expected_msg = (
        "Value 'henry' for author is not in the allowed list: ['peter', 'joel', 'mark']"
    )
    assert e.value.message == expected_msg


def test_fails_any_and_no_blanks():
    with pytest.raises(ValidationError) as e:
        _validate(SCHEMA_ANY_NO_BLANKS, {"author": [""]})
    expected_msg = "Value for author is blank, and that is not allowed"
    assert e.value.message == expected_msg


def test_fails_values_and_no_blanks():
    with pytest.raises(ValidationError) as e:
        _validate(SCHEMA_VALUES_NO_BLANKS, {"author": ["henry"]})
    expected_msg = (
        "Value 'henry' for author is not in the allowed list: ['peter', 'joel', 'mark']"
    )
    assert e.value.message == expected_msg

    with pytest.raises(ValidationError) as e:
        _validate(SCHEMA_VALUES_NO_BLANKS, {"author": [""]})
    expected_msg = "Value for author is blank, and that is not allowed"
    assert e.value.message == expected_msg
