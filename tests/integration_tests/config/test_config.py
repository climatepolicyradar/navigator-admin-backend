from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db

EXPECTED_CCLW_TAXONOMY = {"color", "size"}
EXPECTED_CCLW_COLOURS = ["green", "red", "pink", "blue"]
EXPECTED_UNFCCC_TAXONOMY = {"author", "author_type"}


def test_get_config_has_expected_keys(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    keys = data.keys()

    assert "geographies" in keys
    assert "corpora" in keys
    assert "languages" in keys
    assert "document" in keys
    assert "event" in keys


def test_get_config_has_correct_number_corpora_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the data
    assert len(data["corpora"]) == 2


def test_get_config_has_correct_number_corpora_cclw(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the data
    assert len(data["corpora"]) == 1


def test_get_config_has_correct_number_corpora_unfccc(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the data
    assert len(data["corpora"]) == 1


def test_get_config_cclw_corpora_correct(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the new corpora data
    cclw_corporas = data["corpora"]
    assert len(data["corpora"]) == 1

    assert cclw_corporas[0]["corpus_import_id"] == "CCLW.corpus.i00000001.n0000"
    assert cclw_corporas[0]["corpus_type"] == "Laws and Policies"
    assert cclw_corporas[0]["corpus_type_description"] == "Laws and policies"
    assert cclw_corporas[0]["description"] == "CCLW national policies"
    assert cclw_corporas[0]["title"] == "CCLW national policies"

    cclw_taxonomy = cclw_corporas[0]["taxonomy"]
    expected_cclw_taxonomy = {
        "topic",
        "keyword",
        "hazard",
        "framework",
        "sector",
        "instrument",
    }
    expected_cclw_taxonomy.add("event_types")
    assert set(cclw_taxonomy) ^ expected_cclw_taxonomy == set()


def test_get_config_unfccc_corpora_correct(
    client: TestClient, data_db: Session, non_cclw_user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=non_cclw_user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the new corpora data
    unfccc_corporas = data["corpora"]
    assert len(data["corpora"]) == 1

    assert unfccc_corporas[0]["corpus_import_id"] == "UNFCCC.corpus.i00000001.n0000"
    assert unfccc_corporas[0]["corpus_type"] == "Intl. agreements"
    assert unfccc_corporas[0]["corpus_type_description"] == "Intl. agreements"
    assert unfccc_corporas[0]["description"] == "UNFCCC Submissions"
    assert unfccc_corporas[0]["title"] == "UNFCCC Submissions"

    expected_unfccc_taxonomy = {"author", "author_type"}
    expected_unfccc_taxonomy.add("event_types")
    assert set(unfccc_corporas[0]["taxonomy"]) ^ expected_unfccc_taxonomy == set()


def test_get_config_corpora_correct(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the new corpora data
    corpora = data["corpora"]

    assert corpora[0]["corpus_import_id"] == "CCLW.corpus.i00000001.n0000"
    assert corpora[0]["corpus_type"] == "Laws and Policies"
    assert corpora[0]["corpus_type_description"] == "Laws and policies"
    assert corpora[0]["description"] == "CCLW national policies"
    assert corpora[0]["title"] == "CCLW national policies"

    cclw_taxonomy = corpora[0]["taxonomy"]
    expected_cclw_taxonomy = {
        "topic",
        "keyword",
        "hazard",
        "framework",
        "sector",
        "instrument",
    }
    expected_cclw_taxonomy.add("event_types")
    assert set(cclw_taxonomy) ^ expected_cclw_taxonomy == set()

    assert corpora[1]["corpus_import_id"] == "UNFCCC.corpus.i00000001.n0000"
    assert corpora[1]["corpus_type"] == "Intl. agreements"
    assert corpora[1]["corpus_type_description"] == "Intl. agreements"
    assert corpora[1]["description"] == "UNFCCC Submissions"
    assert corpora[1]["title"] == "UNFCCC Submissions"

    expected_unfccc_taxonomy = {"author", "author_type"}
    expected_unfccc_taxonomy.add("event_types")
    assert set(corpora[1]["taxonomy"]) ^ expected_unfccc_taxonomy == set()


def test_config_languages(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the data
    #
    # Languages.
    assert "aaa" in data["languages"].keys()


def test_config_documents(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the data
    #
    # Documents..
    assert "AMENDMENT" in data["document"]["roles"]
    assert "Action Plan" in data["document"]["types"]
    assert "Translation" in data["document"]["variants"]


def test_config_events(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the data
    #
    # Events.
    assert "Appealed" in data["event"]["types"]


def test_config_geographies(client: TestClient, data_db: Session, user_header_token):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the data
    #
    # Geographies.
    assert data["geographies"][1]["node"]["slug"] == "south-asia"
