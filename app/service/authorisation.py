from app.errors import AuthorisationError
from app.model.jwt_user import JWTUser


OPERATIONS_NEEDING_ADMIN = ["delete_family"]


def is_authorised(user: JWTUser, operation: str) -> None:
    user_auth = user.authorisation

    if operation not in OPERATIONS_NEEDING_ADMIN:
        return

    # If we get here we need an admin
    if (
        user_auth is not None
        and "is_admin" in user_auth.keys()
        and user_auth["is_admin"] is True
    ):
        return

    raise AuthorisationError(f"User {user.email} is not authorised for {operation}")
