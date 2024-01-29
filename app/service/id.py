import re

from db_client.errors import ValidationError

_ID_ELEMENT = r"[a-zA-Z0-9]+([-_]?[a-zA-Z0-9]+)*"
IMPORT_ID_MATCHER = re.compile(
    rf"^{_ID_ELEMENT}\.{_ID_ELEMENT}\.{_ID_ELEMENT}\.{_ID_ELEMENT}$"
)


def validate(import_id: str) -> None:
    if IMPORT_ID_MATCHER.match(import_id) is not None:
        return

    raise ValidationError(f"The import id {import_id} is invalid!")


def validate_multiple_ids(import_ids: set[str]) -> None:
    invalid_ids = [
        import_id
        for import_id in import_ids
        if IMPORT_ID_MATCHER.match(import_id) is None
    ]

    if len(invalid_ids) > 0:
        invalid_ids.sort()
        raise ValidationError(f"The import ids are invalid: {invalid_ids}")
