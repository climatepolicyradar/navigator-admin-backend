from navigator_db_client.models.law_policy.family import FamilyCategory
from navigator_db_client.errors import ValidationError


def validate(category: str) -> str:
    try:
        return FamilyCategory(category).name
    except ValueError as e:
        raise ValidationError(str(e))
