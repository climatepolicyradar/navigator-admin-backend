from typing import cast

import jwt
import pytest

import app.service.token as token_service
from app.errors import TokenError


@pytest.mark.parametrize(
    "email",
    ["e1@here.com", "e2@there.com", "e3@nowhere.com"],
)
@pytest.mark.parametrize(
    "org_id",
    [1, 2, 3],
)
@pytest.mark.parametrize(
    "is_superuser",
    [False, True, False],
)
@pytest.mark.parametrize(
    "authorisation",
    [{}, {"e2": False}, {"e3": {"a": 1}}],
)
def test_ok_when_encoded_and_decoded(
    email: str, org_id: int, is_superuser: bool, authorisation: dict
):
    token = token_service.encode(email, org_id, is_superuser, authorisation)
    assert token is not None
    assert len(token) > 200
    user = token_service.decode(token)
    assert user.email == email
    assert user.is_superuser == is_superuser
    assert user.authorisation == authorisation
    assert user.org_id == org_id


def test_encode_checks_authorisation():
    with pytest.raises(TokenError) as e:
        token_service.encode("email@here.com", 1, False, cast(dict, "random stuff"))

    assert (
        e.value.message == "Parameter authorisation should be a dict, not random stuff"
    )


def test_encode_checks_email():
    with pytest.raises(TokenError) as e:
        token_service.encode("email.here.com", 1, False, {})

    assert e.value.message == "Parameter email should be an email, not email.here.com"


def test_encode_checks_is_superuser():
    with pytest.raises(TokenError) as e:
        token_service.encode("email@here.com", 1, cast(bool, "False"), {})

    assert e.value.message == "Parameter is_superuser should be a bool, not False"


def test_decode_fails_when_empty():
    with pytest.raises(TokenError) as e:
        token_service.decode("")

    assert e.value.message == "Error when decoding token: Not enough segments"


def test_decode_fails_when_no_email():
    encoded_jwt = jwt.encode(
        {}, token_service.SECRET_KEY, algorithm=token_service.ALGORITHM
    )
    with pytest.raises(TokenError) as e:
        token_service.decode(encoded_jwt)

    assert e.value.message == "Token did not contain an email"


def test_decode_fails_when_no_org_id():
    encoded_jwt = jwt.encode(
        {"email": "bob@here.com", "is_superuser": False, "authorisation": {}},
        token_service.SECRET_KEY,
        algorithm=token_service.ALGORITHM,
    )

    with pytest.raises(TokenError) as e:
        token_service.decode(encoded_jwt)

    assert e.value.message == "Token did not contain an organisation_id"
