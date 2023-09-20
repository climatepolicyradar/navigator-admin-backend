import logging
from app.errors import ValidationError
from app.model.general import Json
from sqlalchemy.orm import Session
from app.repository import metadata_repo

_LOGGER = logging.getLogger(__name__)

KEY_ALLOW_ANY = "allow_any"
KEY_ALLOW_BLANKS = "allow_blanks"
KEY_ALLOWED_VALUES = "allowed_values"

"""
Behaviour:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~...
| allow_any | allow_blanks  | Behaviour
---------------------------------------...
| True      | True          | allowed_values is ignored and anything goes
| True      | False         | allowed_values is ignored but you need a non-blank value
| False     | True          | allowed_values is used to validate, blank is also valid
| False     | False         | allowed_values is used to validate, blank is invalid
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~...
"""
VALID_SCHEMA_KEYS = [KEY_ALLOW_ANY, KEY_ALLOW_BLANKS, KEY_ALLOWED_VALUES]


def validate(db: Session, org_id: int, data: Json) -> bool:
    schema = metadata_repo.get_schema_for_org(db, org_id)
    if schema is None:
        msg = f"Organisation {org_id} has no Taxonomy defined!"
        _LOGGER.error(msg)
        raise ValidationError(msg)
    return _validate(schema, data)


def _validate(schema: Json, data: Json) -> bool:
    """
    Validates the data against the schema

    :param Json schema: The schema to use for the validation
    :param Json data: The values to use
    :return bool: True if valid, False if not
    :raises ValidationError: _description_
    """
    # TODO : use pydantic

    # Quick schema validation first
    valid_data_keys = _validate_schema(schema)

    missing_data_keys = set(valid_data_keys).difference(set(data.keys()))

    if len(missing_data_keys) > 0:
        msg = f"Values for the following are missing: {missing_data_keys}"
        _LOGGER.error(msg)
        raise ValidationError(msg)

    _validate_data(schema, data, valid_data_keys)

    return True


def _validate_data(schema, data, valid_data_keys):
    for key, values_list in data.items():
        # First check key is valid against those in the schema
        if key not in valid_data_keys:
            msg = f"Unknown '{key}' not in {valid_data_keys}"
            _LOGGER.error(msg)
            raise ValidationError(msg)

        key_schema = schema[key]

        _validate_values(key_schema, key, values_list)


def _validate_values(key_schema, key, values_list):
    for value in values_list:
        allow_blanks = (
            True
            if KEY_ALLOW_BLANKS in key_schema and key_schema[KEY_ALLOW_BLANKS] is True
            else False
        )

        if value == "":
            if allow_blanks:
                continue
            msg = f"Value for {key} is blank, and that is not allowed"
            _LOGGER.error(msg)
            raise ValidationError(msg)

        allow_any = (
            True
            if KEY_ALLOW_ANY in key_schema and key_schema[KEY_ALLOW_ANY] is True
            else False
        )

        if allow_any:
            continue

        valid_values = key_schema[KEY_ALLOWED_VALUES]
        if value not in valid_values:
            msg = (
                f"Value '{value}' for {key} is not in the allowed list: {valid_values}"
            )
            _LOGGER.error(msg)
            raise ValidationError(msg)


def _validate_schema(schema):
    valid_data_keys = []
    for key, value in schema.items():
        valid_data_keys.append(key)

        # Check the schema has the values we expect
        values = [k for k in value.keys()]
        unknown_values = set(values).difference(set(VALID_SCHEMA_KEYS))

        # Raise if any unknown ones
        if len(unknown_values) > 0:
            msg = f"Unknown values in schema: {unknown_values}"
            _LOGGER.error(msg)
            raise ValueError(msg)

        # TODO: The following is too simplistic as certain sub-sets are valid
        # missing_values = set(VALID_SCHEMA_KEYS).difference(set(values))
        # # Raise if any missing ones
        # if len(missing_values) > 0:
        #     raise ValueError(f"Missing values in schema: {missing_values}")

    return valid_data_keys
