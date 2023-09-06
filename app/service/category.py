from app.db.models.law_policy.family import FamilyCategory
from app.errors import ValidationError


def validate(category: str) -> str:
    try:
        return FamilyCategory(category).name
    except ValueError as e:
        raise ValidationError(str(e))
