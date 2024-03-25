from db_client.models.dfce.family import FamilyCategory

from app.errors import ValidationError


def validate(category: str) -> str:
    try:
        return FamilyCategory(category).name
    except ValueError as e:
        raise ValidationError(str(e))
