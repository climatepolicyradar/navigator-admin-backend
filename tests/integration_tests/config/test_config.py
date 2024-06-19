from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import setup_db

EXPECTED_CONFIG_KEYS = {"geographies", "corpora", "languages", "document", "event"}
EXPECTED_CORPORA_CONFIG_KEYS = {
    "corpus_import_id",
    "title",
    "description",
    "corpus_type",
    "corpus_type_description",
    "organisation",
    "taxonomy",
}
EXPECTED_GEOGRAPHY_REGIONS = 8
EXPECTED_LANGUAGES = 7893

EXPECTED_CCLW_TAXONOMY = {
    "topic",
    "keyword",
    "hazard",
    "framework",
    "sector",
    "instrument",
    "event_types",
}
EXPECTED_CCLW_TOPICS = 4
EXPECTED_CCLW_HAZARDS = 81
EXPECTED_CCLW_SECTORS = 23
EXPECTED_CCLW_KEYWORDS = 219
EXPECTED_CCLW_FRAMEWORKS = 3
EXPECTED_CCLW_INSTRUMENTS = 25

EXPECTED_UNFCCC_TAXONOMY = {"author", "author_type", "event_types"}


def test_get_config_has_expected_shape(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert set(data.keys()) ^ EXPECTED_CONFIG_KEYS == set()

    assert isinstance(data["geographies"], list)
    assert len(data["geographies"]) == EXPECTED_GEOGRAPHY_REGIONS

    assert isinstance(data["corpora"], list)
    assert set(data["corpora"][0].keys()) ^ EXPECTED_CORPORA_CONFIG_KEYS == set()
    assert list(data["corpora"][0]["organisation"]) == ["id", "name"]

    assert isinstance(data["languages"], dict)
    assert len(data["languages"]) == EXPECTED_LANGUAGES

    assert isinstance(data["document"], dict)
    assert list(data["document"].keys()) == ["roles", "types", "variants"]

    assert isinstance(data["event"], dict)
    assert list(data["event"].keys()) == ["types"]


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
    assert set(cclw_taxonomy) ^ EXPECTED_CCLW_TAXONOMY == set()

    assert len(cclw_taxonomy["topic"]["allowed_values"]) == EXPECTED_CCLW_TOPICS
    assert len(cclw_taxonomy["hazard"]["allowed_values"]) == EXPECTED_CCLW_HAZARDS
    assert len(cclw_taxonomy["sector"]["allowed_values"]) == EXPECTED_CCLW_SECTORS
    assert len(cclw_taxonomy["framework"]["allowed_values"]) == EXPECTED_CCLW_FRAMEWORKS
    assert len(cclw_taxonomy["keyword"]["allowed_values"]) == EXPECTED_CCLW_KEYWORDS
    assert (
        len(cclw_taxonomy["instrument"]["allowed_values"]) == EXPECTED_CCLW_INSTRUMENTS
    )


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

    unfccc_taxonomy = unfccc_corporas[0]["taxonomy"]
    assert set(unfccc_taxonomy) ^ EXPECTED_UNFCCC_TAXONOMY == set()


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
    assert set(cclw_taxonomy) ^ EXPECTED_CCLW_TAXONOMY == set()

    assert len(cclw_taxonomy["topic"]["allowed_values"]) == EXPECTED_CCLW_TOPICS
    assert len(cclw_taxonomy["hazard"]["allowed_values"]) == EXPECTED_CCLW_HAZARDS
    assert len(cclw_taxonomy["sector"]["allowed_values"]) == EXPECTED_CCLW_SECTORS
    assert len(cclw_taxonomy["framework"]["allowed_values"]) == EXPECTED_CCLW_FRAMEWORKS
    assert len(cclw_taxonomy["keyword"]["allowed_values"]) == EXPECTED_CCLW_KEYWORDS
    assert (
        len(cclw_taxonomy["instrument"]["allowed_values"]) == EXPECTED_CCLW_INSTRUMENTS
    )

    assert corpora[1]["corpus_import_id"] == "UNFCCC.corpus.i00000001.n0000"
    assert corpora[1]["corpus_type"] == "Intl. agreements"
    assert corpora[1]["corpus_type_description"] == "Intl. agreements"
    assert corpora[1]["description"] == "UNFCCC Submissions"
    assert corpora[1]["title"] == "UNFCCC Submissions"

    unfccc_taxonomy = corpora[1]["taxonomy"]
    assert set(unfccc_taxonomy) ^ EXPECTED_UNFCCC_TAXONOMY == set()


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
