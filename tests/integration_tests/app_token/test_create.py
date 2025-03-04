import os
from datetime import datetime
from typing import cast
from unittest import mock

import pytest
from db_client.models.organisation.corpus import Corpus
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.model.app_token import AppTokenReadDTO
from app.service.app_token import decode
from tests.helpers.app_token import (
    EXPIRE_AFTER_1_YEAR,
    EXPIRE_AFTER_5_YEARS,
    EXPIRE_AFTER_DEFAULT_YEARS,
    create_custom_app_create_dto,
    has_expected_keys,
    timedelta_years,
)
from tests.integration_tests.setup_db import setup_db


@pytest.fixture()
def set_env_var(monkeypatch):
    with mock.patch.dict(os.environ, clear=True):
        envvars = {
            "TOKEN_SECRET_KEY": "test_key",
        }
        for k, v in envvars.items():
            monkeypatch.setenv(k, v)
        yield  # This is the magical bit which restores the environment after


def test_create_app_token_default_expiry(
    client: TestClient, data_db: Session, superuser_header_token, set_env_var
):
    setup_db(data_db)
    test_token = create_custom_app_create_dto(
        ["UNFCCC.corpus.i00000001.n0000", "CCLW.corpus.i00000001.n0000"]
    )
    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, str)

    decoded_data = decode(data)
    decoded_data_dto = AppTokenReadDTO(**decoded_data)  # type: ignore
    assert has_expected_keys(list(cast(dict, decoded_data).keys()))
    assert decoded_data_dto.allowed_corpora_ids == [
        "CCLW.corpus.i00000001.n0000",
        "UNFCCC.corpus.i00000001.n0000",
    ]
    assert decoded_data_dto.sub == "TEST"
    assert decoded_data_dto.aud == "example.test.org"
    assert decoded_data_dto.iss == "Climate Policy Radar"
    assert timedelta_years(
        EXPIRE_AFTER_DEFAULT_YEARS,
        datetime.fromtimestamp(cast(float, decoded_data_dto.exp)),
    ) == datetime.fromtimestamp(decoded_data_dto.iat)

    assert not cast(str, decoded_data_dto.aud).endswith("/")
    assert "://" not in cast(str, decoded_data_dto.aud)
    assert not cast(str, decoded_data_dto.aud).startswith("http")


@pytest.mark.parametrize("expiry_years", [EXPIRE_AFTER_1_YEAR, EXPIRE_AFTER_5_YEARS])
def test_create_app_token_specific_expiry(
    client: TestClient,
    data_db: Session,
    superuser_header_token,
    expiry_years: int,
    set_env_var,
):
    setup_db(data_db)
    test_token = create_custom_app_create_dto(
        ["UNFCCC.corpus.i00000001.n0000", "CCLW.corpus.i00000001.n0000"],
        expiry_years=expiry_years,
    )

    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, str)

    decoded_data = decode(data)
    decoded_data_dto = AppTokenReadDTO(**decoded_data)  # type: ignore
    assert has_expected_keys(list(cast(dict, decoded_data).keys()))
    assert decoded_data_dto.allowed_corpora_ids == [
        "CCLW.corpus.i00000001.n0000",
        "UNFCCC.corpus.i00000001.n0000",
    ]
    assert decoded_data_dto.sub == "TEST"
    assert decoded_data_dto.aud == "example.test.org"
    assert decoded_data_dto.iss == "Climate Policy Radar"
    assert timedelta_years(
        expiry_years, datetime.fromtimestamp(cast(float, decoded_data_dto.exp))
    ) == datetime.fromtimestamp(decoded_data_dto.iat)

    assert not cast(str, decoded_data_dto.aud).endswith("/")
    assert "://" not in cast(str, decoded_data_dto.aud)
    assert not cast(str, decoded_data_dto.aud).startswith("http")


def test_create_app_token_allows_empty_corpora_list(
    client: TestClient, data_db: Session, superuser_header_token, set_env_var
):
    setup_db(data_db)
    test_token = create_custom_app_create_dto()
    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data, str)

    decoded_data = decode(data)
    decoded_data_dto = AppTokenReadDTO(**decoded_data)  # type: ignore
    assert has_expected_keys(list(cast(dict, decoded_data).keys()))
    assert decoded_data_dto.allowed_corpora_ids == []
    assert decoded_data_dto.sub == "TEST"
    assert decoded_data_dto.aud == "example.test.org"
    assert decoded_data_dto.iss == "Climate Policy Radar"
    assert timedelta_years(
        EXPIRE_AFTER_DEFAULT_YEARS,
        datetime.fromtimestamp(cast(float, decoded_data_dto.exp)),
    ) == datetime.fromtimestamp(decoded_data_dto.iat)

    assert not cast(str, decoded_data_dto.aud).endswith("/")
    assert "://" not in cast(str, decoded_data_dto.aud)
    assert not cast(str, decoded_data_dto.aud).startswith("http")


@pytest.mark.parametrize(
    "subject",
    [
        ("@a9*7g$;"),
        ("some subject;"),
    ],
)
def test_create_app_token_subject_contains_special_chars(
    subject: str,
    client: TestClient,
    data_db: Session,
    superuser_header_token,
    set_env_var,
):
    setup_db(data_db)
    test_token = create_custom_app_create_dto(theme=subject)
    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert data["detail"] == "Invalid subject provided"


def test_create_app_token_when_a_corpus_does_not_exist(
    client: TestClient, data_db: Session, superuser_header_token, set_env_var
):
    setup_db(data_db)
    test_token = create_custom_app_create_dto(["CCLW.corpus.i00000002.n0000"])
    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = response.json()
    assert data["detail"] == "One or more import IDs don't exist"

    actual_corpus = (
        data_db.query(Corpus)
        .filter(Corpus.import_id == "CCLW.corpus.i00000002.n0000")
        .one_or_none()
    )
    assert actual_corpus is None


def test_create_app_token_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    test_token = create_custom_app_create_dto()
    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_app_token_non_admin_non_super(client: TestClient, user_header_token):
    test_token = create_custom_app_create_dto()
    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"] == "User cclw@cpr.org is not authorised to CREATE an APP_TOKEN"
    )


def test_create_app_token_admin_non_super(client: TestClient, admin_user_header_token):
    test_token = create_custom_app_create_dto()
    response = client.post(
        "/api/v1/app-tokens",
        json=test_token.model_dump(mode="json"),
        headers=admin_user_header_token,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert (
        data["detail"] == "User admin@cpr.org is not authorised to CREATE an APP_TOKEN"
    )
