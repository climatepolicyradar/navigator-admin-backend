import re

from app.errors.validation_error import ValidationError

_ID_ELEMENT = r"[a-zA-Z0-9]+([-_]?[a-zA-Z0-9]+)*"
IMPORT_ID_MATCHER = re.compile(
    rf"^{_ID_ELEMENT}\.{_ID_ELEMENT}\.{_ID_ELEMENT}\.{_ID_ELEMENT}$"
)


def validate(import_id: str) -> None:
    if IMPORT_ID_MATCHER.match(import_id) is not None:
        return

    raise ValidationError(f"The import id {import_id} is invalid!")
