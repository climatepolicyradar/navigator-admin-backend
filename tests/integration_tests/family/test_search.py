import logging
from typing import cast

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.integration_tests.setup_db import DBEntry, add_data, setup_db


def test_search_geographies(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    add_data(
        data_db,
        [
            {
                "import_id": "A.0.0.4",
                "title": "title",
                "summary": "gregarious magazine rub",
                "geography": "ALB",
                "geographies": ["ALB"],
                "category": "UNFCCC",
                "status": "Created",
                "metadata": {"author": ["CPR"], "author_type": ["Party"]},
                "organisation": "UNFCCC",
                "corpus_import_id": "UNFCCC.corpus.i00000001.n0000",
                "corpus_title": "UNFCCC Submissions",
                "corpus_type": "Intl. agreements",
                "slug": "Slug4",
                "events": ["E.0.0.3"],
                "published_date": "2018-12-24T04:59:33Z",
                "last_updated_date": "2018-12-24T04:59:33Z",
                "documents": ["D.0.0.1", "D.0.0.2"],
                "collections": ["C.0.0.4"],
                "concepts": [],
            },
            {
                "import_id": "A.0.0.5",
                "title": "title",
                "summary": "flour umbrella established",
                "geography": "ZMB",
                "geographies": ["ZMB"],
                "category": "UNFCCC",
                "status": "Created",
                "metadata": {"author": ["CPR"], "author_type": ["Party"]},
                "organisation": "UNFCCC",
                "corpus_import_id": "UNFCCC.corpus.i00000001.n0000",
                "corpus_title": "UNFCCC Submissions",
                "corpus_type": "Intl. agreements",
                "slug": "Slug5",
                "events": ["E.0.0.3"],
                "published_date": "2018-12-24T04:59:33Z",
                "last_updated_date": "2018-12-24T04:59:33Z",
                "documents": ["D.0.0.1", "D.0.0.2"],
                "collections": ["C.0.0.4"],
                "concepts": [],
            },
        ],
    )

    tests_cases = [
        (["Afghanistan"], ["A.0.0.1", "A.0.0.3"]),
        (["Zimbabwe"], ["A.0.0.2"]),
        (["Albania", "Zambia"], ["A.0.0.4", "A.0.0.5"]),
    ]

    for countries, expected_ids in tests_cases:
        geographies_query = "&".join([f"geography={country}" for country in countries])
        response = client.get(
            f"/api/v1/families/?{geographies_query}",
            headers=superuser_header_token,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        ids = [result["import_id"] for result in data]
        assert isinstance(data, list)
        assert ids == expected_ids


def test_search_retrieves_families_with_multiple_geographies(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    add_data(
        data_db,
        [
            {
                "import_id": "A.0.0.4",
                "title": "title",
                "summary": "gregarious magazine rub",
                "geography": "ALB",
                "geographies": ["ALB", "USA", "BRB"],
                "category": "UNFCCC",
                "status": "Created",
                "metadata": {"author": ["CPR"], "author_type": ["Party"]},
                "organisation": "UNFCCC",
                "corpus_import_id": "UNFCCC.corpus.i00000001.n0000",
                "corpus_title": "UNFCCC Submissions",
                "corpus_type": "Intl. agreements",
                "slug": "Slug4",
                "events": ["E.0.0.3"],
                "published_date": "2018-12-24T04:59:33Z",
                "last_updated_date": "2018-12-24T04:59:33Z",
                "documents": ["D.0.0.1", "D.0.0.2"],
                "collections": ["C.0.0.4"],
                "concepts": [],
            },
            {
                "import_id": "A.0.0.5",
                "title": "title",
                "summary": "flour umbrella established",
                "geography": "AGO",
                "geographies": ["AGO", "ALB"],
                "category": "UNFCCC",
                "status": "Created",
                "metadata": {"author": ["CPR"], "author_type": ["Party"]},
                "organisation": "UNFCCC",
                "corpus_import_id": "UNFCCC.corpus.i00000001.n0000",
                "corpus_title": "UNFCCC Submissions",
                "corpus_type": "Intl. agreements",
                "slug": "Slug5",
                "events": ["E.0.0.3"],
                "published_date": "2018-12-24T04:59:33Z",
                "last_updated_date": "2018-12-24T04:59:33Z",
                "documents": ["D.0.0.1", "D.0.0.2"],
                "collections": ["C.0.0.4"],
                "concepts": [],
            },
        ],
    )

    test_geography = {"display_name": "Albania", "iso_code": "ALB"}

    geographies_query = f"&geography={test_geography['display_name']}"
    response = client.get(
        f"/api/v1/families/?{geographies_query}",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for item in data:
        assert "geographies" in item
        assert isinstance(item["geographies"], list)
        assert test_geography["iso_code"] in item["geographies"]


def test_search_excludes_future_events_when_returning_last_updated_date(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    family_with_future_event = next(
        (item for item in data if item["import_id"] == "A.0.0.3"), None
    )
    assert family_with_future_event is not None
    assert "last_updated_date" in family_with_future_event
    assert family_with_future_event["last_updated_date"] == "2018-12-24T04:59:33Z"
    assert family_with_future_event["events"] == ["E.0.0.3", "E.0.0.4"]


def test_search_family_super(
    client: TestClient, data_db: Session, superuser_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/?q=orange",
        headers=superuser_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 2

    expected_ids = set(["A.0.0.2", "A.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_non_super(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/?q=orange",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["A.0.0.2"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_with_specific_param(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/?summary=apple",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    expected_ids = set(["A.0.0.2"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_with_max_results(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/?q=orange&max_results=1",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 1

    # We cannot check the id returned as although the search is ordered
    # it is based on modified time which can be the same.


def test_search_family_when_not_authenticated(client: TestClient, data_db: Session):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/?q=orange",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_search_family_when_not_found(
    client: TestClient, data_db: Session, user_header_token, caplog
):
    setup_db(data_db)
    with caplog.at_level(logging.INFO):
        response = client.get(
            "/api/v1/families/?q=chicken",
            headers=user_header_token,
        )
    assert response.status_code == status.HTTP_200_OK
    assert (
        "Families not found for terms: {'q': 'chicken', 'max_results': 500}"
        in caplog.text
    )


def test_search_family_when_invalid_params(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/?wrong=param",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "Search parameters are invalid: ['wrong']"


def test_search_family_when_db_error(
    client: TestClient, data_db: Session, bad_family_repo, user_header_token
):
    setup_db(data_db)
    response = client.get(
        "/api/v1/families/?q=error",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    data = response.json()
    assert data["detail"] == "Bad Repo"
    assert bad_family_repo.search.call_count == 1


def test_search_family_without_collections(
    client: TestClient, data_db: Session, user_header_token
):
    setup_db(data_db)
    # Add a family with no collections
    family_without_collections = {
        "import_id": "A.0.0.99",
        "title": "no collection family",
        "summary": "family without any collection",
        "geography": "AFG",
        "geographies": ["AFG"],
        "category": "UNFCCC",
        "status": "Created",
        "metadata": {
            "topic": [],
            "hazard": [],
            "sector": [],
            "keyword": [],
            "framework": [],
            "instrument": [],
        },
        "organisation": "CCLW",
        "corpus_import_id": "CCLW.corpus.i00000001.n0000",
        "corpus_title": "CCLW national policies",
        "corpus_type": "Laws and Policies",
        "slug": "no-collection-slug",
        "events": [],
        "published_date": None,
        "last_updated_date": None,
        "documents": [],
        "collections": [],
        "concepts": [],
    }
    add_data(data_db, [cast(DBEntry, family_without_collections)])

    # Search for all families
    response = client.get(
        "/api/v1/families/?q=",
        headers=user_header_token,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    found = next((f for f in data if f["import_id"] == "A.0.0.99"), None)
    assert found is not None, "Family without collections should be present in results"
    assert "collections" in found
    assert (
        found["collections"] == []
    ), "Collections field should be an empty list for families without collections"
