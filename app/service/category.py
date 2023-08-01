from app.db.models.law_policy.family import FamilyCategory
from app.errors.validation_error import ValidationError


def validate(category: str) -> str:
    try:
        return FamilyCategory(category).name
    except ValueError as e:
        raise ValidationError(str(e))
