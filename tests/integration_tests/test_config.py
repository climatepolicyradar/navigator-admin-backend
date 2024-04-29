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
    assert "taxonomies" in keys
    assert "languages" in keys
    assert "document" in keys
    assert "event" in keys


def test_get_config_has_correct_organisations(
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
    #
    # Organisations.
    LEN_ORG_CONFIG = 2

    assert "CCLW" in data["taxonomies"].keys()
    cclw_org = data["taxonomies"]["CCLW"]
    assert len(cclw_org) == LEN_ORG_CONFIG

    assert "UNFCCC" in data["taxonomies"]
    unfccc_org = data["taxonomies"]["UNFCCC"]
    assert len(unfccc_org) == LEN_ORG_CONFIG


# TODO: Remove as part of PDCT-1052
def test_get_config_cclw_old_taxonomy_correct(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the old taxonomy data
    assert "CCLW" in data["taxonomies"].keys()
    cclw_org = data["taxonomies"]["CCLW"]
    assert len(cclw_org) == 2

    cclw_taxonomy = cclw_org["taxonomy"]
    assert set(cclw_taxonomy) == EXPECTED_CCLW_TAXONOMY
    cclw_taxonomy_colours = cclw_taxonomy["color"]["allowed_values"]
    assert set(cclw_taxonomy_colours) ^ set(EXPECTED_CCLW_COLOURS) == set()


# TODO: Remove as part of PDCT-1052
def test_get_config_unfccc_old_taxonomy_correct(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)

    response = client.get(
        "/api/v1/config",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Now sanity check the old taxonomy data
    assert "UNFCCC" in data["taxonomies"]
    unfccc_org = data["taxonomies"]["UNFCCC"]
    assert len(unfccc_org) == 2

    unfccc_taxonomy = unfccc_org["taxonomy"]
    assert set(unfccc_taxonomy) == EXPECTED_UNFCCC_TAXONOMY
    assert set(unfccc_taxonomy["author_type"]["allowed_values"]) == {
        "Party",
        "Non-Party",
    }


def test_get_config_cclw_new_taxonomy_correct(
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
    assert "CCLW" in data["taxonomies"].keys()
    cclw_org = data["taxonomies"]["CCLW"]
    assert len(cclw_org) == 2

    EXPECTED_CCLW_TAXONOMY.add("event_types")

    cclw_corpora = cclw_org["corpora"]
    assert len(cclw_corpora) == 1
    assert cclw_corpora[0]["corpus_import_id"] == "CCLW.corpus.i00000001.n0000"
    assert cclw_corpora[0]["corpus_type"] == "Laws and Policies"
    assert cclw_corpora[0]["corpus_type_description"] == "Laws and policies"
    assert cclw_corpora[0]["description"] == "CCLW national policies"
    assert cclw_corpora[0]["title"] == "CCLW national policies"
    assert set(cclw_corpora[0]["taxonomy"]) ^ EXPECTED_CCLW_TAXONOMY == set()


def test_get_config_unfccc_new_taxonomy_correct(
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
    assert "UNFCCC" in data["taxonomies"]
    unfccc_org = data["taxonomies"]["UNFCCC"]
    assert len(unfccc_org) == 2

    EXPECTED_UNFCCC_TAXONOMY.add("event_types")

    unfccc_corpora = unfccc_org["corpora"]
    assert len(unfccc_corpora) == 1
    assert unfccc_corpora[0]["corpus_import_id"] == "UNFCCC.corpus.i00000001.n0000"
    assert unfccc_corpora[0]["corpus_type"] == "Intl. agreements"
    assert unfccc_corpora[0]["corpus_type_description"] == "Intl. agreements"
    assert unfccc_corpora[0]["description"] == "UNFCCC Submissions"
    assert unfccc_corpora[0]["title"] == "UNFCCC Submissions"
    assert set(unfccc_corpora[0]["taxonomy"]) ^ EXPECTED_UNFCCC_TAXONOMY == set()


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
