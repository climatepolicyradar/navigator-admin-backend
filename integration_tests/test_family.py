from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models.app.users import Organisation
from app.db.models.law_policy.family import (
    Family,
    FamilyCategory,
    FamilyOrganisation,
    Slug,
)
from app.db.models.law_policy.metadata import (
    FamilyMetadata,
    MetadataOrganisation,
    MetadataTaxonomy,
)
from unit_tests.helpers.family import create_family_dto


EXPECTED_FAMILIES = [
    {
        "import_id": "A.0.0.1",
        "title": "apple",
        "summary": "",
        "geography": "South Asia",
        "category": "UNFCCC",
        "status": "Created",
        "metadata": {"size": 3, "color": "red"},
        "organisation": "test_org",
        "slug": "",
        "events": [],
        "published_date": None,
        "last_updated_date": None,
        "documents": [],
        "collections": [],
    },
    {
        "import_id": "A.0.0.2",
        "title": "apple orange banana",
        "summary": "",
        "geography": "South Asia",
        "category": "UNFCCC",
        "status": "Created",
        "metadata": {"size": 4, "color": "green"},
        "organisation": "test_org",
        "slug": "",
        "events": [],
        "published_date": None,
        "last_updated_date": None,
        "documents": [],
        "collections": [],
    },
    {
        "import_id": "A.0.0.3",
        "title": "title",
        "summary": "orange peas",
        "geography": "South Asia",
        "category": "UNFCCC",
        "status": "Created",
        "metadata": {"size": 100, "color": "blue"},
        "organisation": "test_org",
        "slug": "",
        "events": [],
        "published_date": None,
        "last_updated_date": None,
        "documents": [],
        "collections": [],
    },
]


def _setup_db(test_db: Session):
    with open("integration_tests/default-data.sql") as file:
        query = text(file.read())
        test_db.execute(query)

    FAMILY_1 = Family(
        import_id="A.0.0.1",
        title="apple",
        description="",
        geography_id=1,
        family_category=FamilyCategory.UNFCCC,
    )

    FAMILY_2 = Family(
        import_id="A.0.0.2",
        title="apple orange banana",
        description="",
        geography_id=1,
        family_category=FamilyCategory.UNFCCC,
    )

    FAMILY_3 = Family(
        import_id="A.0.0.3",
        title="title",
        description="orange peas",
        geography_id=1,
        family_category=FamilyCategory.UNFCCC,
    )

    test_db.add(FAMILY_1)
    test_db.add(FAMILY_2)
    test_db.add(FAMILY_3)

    # Now an organisation
    org = Organisation(
        name="test_org", description="for testing", organisation_type="testorg"
    )
    test_db.add(org)
    test_db.flush()

    # Link the families to the org
    test_db.add(FamilyOrganisation(family_import_id="A.0.0.1", organisation_id=org.id))
    test_db.add(FamilyOrganisation(family_import_id="A.0.0.2", organisation_id=org.id))
    test_db.add(FamilyOrganisation(family_import_id="A.0.0.3", organisation_id=org.id))

    # Now a Taxonomy
    tax = MetadataTaxonomy(
        description="test meta",
        valid_metadata={
            "color": {
                "allow_any": False,
                "allowed_values": ["green", "red", "pink", "blue"],
            },
            "size": {
                "allow_any": True,
                "allowed_values": [],
            },
        },
    )
    test_db.add(tax)
    test_db.flush()

    # Now a MetadataOrganisation
    mo = MetadataOrganisation(taxonomy_id=tax.id, organisation_id=org.id)
    test_db.add(mo)
    test_db.flush()

    # Now add the metadata onto the families
    test_db.add(
        FamilyMetadata(
            family_import_id="A.0.0.1",
            taxonomy_id=tax.id,
            value={"color": "red", "size": 3},
        )
    )
    test_db.add(
        FamilyMetadata(
            family_import_id="A.0.0.2",
            taxonomy_id=tax.id,
            value={"color": "green", "size": 4},
        )
    )
    test_db.add(
        FamilyMetadata(
            family_import_id="A.0.0.3",
            taxonomy_id=tax.id,
            value={"color": "blue", "size": 100},
        )
    )

    test_db.commit()


# --- GET ALL


def test_get_all_families_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list
    assert len(data) == 3
    ids_found = set([f["import_id"] for f in data])
    expected_ids = set(["A.0.0.1", "A.0.0.2", "A.0.0.3"])

    assert ids_found.symmetric_difference(expected_ids) == set([])

    sdata = sorted(data, key=lambda d: d["import_id"])
    assert sdata[0] == EXPECTED_FAMILIES[0]
    assert sdata[1] == EXPECTED_FAMILIES[1]
    assert sdata[2] == EXPECTED_FAMILIES[2]


# --- GET


def test_get_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A.0.0.1",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["import_id"] == "A.0.0.1"
    assert data == EXPECTED_FAMILIES[0]


def test_get_family_404(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not found: A.0.0.8"


def test_get_family_400(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A008",
    )
    assert response.status_code == 400
    data = response.json()
    expected_msg = "The import id A008 is invalid!"
    assert data["detail"] == expected_msg


def test_get_family_503(client: TestClient, test_db: Session, bad_family_repo):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/A.0.0.8",
    )
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"


# --- SEARCH


def test_search_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=orange",
    )
    assert response.status_code == 200
    data = response.json()
    assert type(data) is list

    ids_found = set([f["import_id"] for f in data])
    assert len(ids_found) == 2

    expected_ids = set(["A.0.0.2", "A.0.0.3"])
    assert ids_found.symmetric_difference(expected_ids) == set([])


def test_search_family_404(client: TestClient, test_db: Session):
    _setup_db(test_db)
    response = client.get(
        "/api/v1/families/?q=chicken",
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Families not found for term: chicken"


# --- UPDATE


def test_update_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.2",
        title="Updated Title",
        summary="just a test",
        geography="USA",
        category=FamilyCategory.UNFCCC,
        metadata={"color": "pink", "size": 0},
        slug="new-slug",
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["summary"] == "just a test"
    assert data["geography"] == "USA"
    assert data["category"] == "UNFCCC"
    assert data["slug"].startswith("updated-title")

    db_family: Family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title == "Updated Title"
    assert db_family.description == "just a test"
    assert db_family.geography_id == 210
    assert db_family.family_category == "UNFCCC"
    db_slug = test_db.query(Slug).filter(Slug.family_import_id == "A.0.0.2").all()
    assert len(db_slug) == 1
    assert str(db_slug[0].name).startswith("updated-title")


def test_update_family_idempotent_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    family = EXPECTED_FAMILIES[1]
    response = client.put("/api/v1/families", json=family)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == EXPECTED_FAMILIES[1]["title"]
    assert data["summary"] == EXPECTED_FAMILIES[1]["summary"]
    assert data["geography"] == EXPECTED_FAMILIES[1]["geography"]
    assert data["category"] == EXPECTED_FAMILIES[1]["category"]
    db_family: Family = (
        test_db.query(Family)
        .filter(Family.import_id == EXPECTED_FAMILIES[1]["import_id"])
        .one()
    )
    assert db_family.title == EXPECTED_FAMILIES[1]["title"]
    assert db_family.description == EXPECTED_FAMILIES[1]["summary"]
    assert db_family.geography_id == 1
    assert db_family.family_category == EXPECTED_FAMILIES[1]["category"]


def test_update_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo
):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.2",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503

    db_family: Family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.2").one()
    )
    assert db_family.title != "Updated Title"
    assert db_family.description != "just a test"

    db_slug = test_db.query(Slug).filter(Slug.family_import_id == "A.0.0.2").all()
    # Ensure no slug was created
    assert len(db_slug) == 0

    db_meta = (
        test_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.2")
        .all()
    )
    # Ensure no metadata was updated
    assert len(db_meta) == 1
    assert db_meta[0].value == {"size": 4, "color": "green"}


def test_update_family_404(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not updated: A.0.0.22"


def test_update_family_503(client: TestClient, test_db: Session, bad_family_repo):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_update_family__invalid_geo_400(
    client: TestClient, test_db: Session, bad_family_repo
):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.22",
        title="Updated Title",
        summary="just a test",
        metadata={"color": "pink", "size": 0},
    )
    new_family.geography = "UK"
    response = client.put("/api/v1/families", json=new_family.dict())
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


def test_update_family_metadata_if_changed(client: TestClient, test_db: Session):
    _setup_db(test_db)
    expected_meta = {"color": "pink", "size": 23}
    response = client.get(
        "/api/v1/families/A.0.0.2",
    )
    assert response.status_code == 200
    family_data = response.json()
    assert {"color": "green", "size": 4} == family_data["metadata"]
    family_data["metadata"] = expected_meta
    response = client.put("/api/v1/families", json=family_data)

    assert response.status_code == 200
    data = response.json()
    assert expected_meta == data["metadata"]

    metadata: FamilyMetadata = (
        test_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.2")
        .one()
    )
    assert metadata.value == expected_meta


# --- CREATE


def test_create_family_200(client: TestClient, test_db: Session):
    _setup_db(test_db)
    test_meta = {"color": "blue", "size": 888}
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
        metadata=test_meta,
    )
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Title"
    assert data["summary"] == "test test test"
    actual_family = test_db.query(Family).filter(Family.import_id == "A.0.0.9").one()
    assert actual_family.title == "Title"
    assert actual_family.description == "test test test"
    metadata = (
        test_db.query(FamilyMetadata)
        .filter(FamilyMetadata.family_import_id == "A.0.0.9")
        .one()
    )
    assert metadata.value is not None
    assert metadata.value == test_meta


def test_create_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo
):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503
    actual_family = (
        test_db.query(Family).filter(Family.import_id == "A.0.0.9").one_or_none()
    )
    assert actual_family is None
    db_slug = test_db.query(Slug).filter(Slug.family_import_id == "A.0.0.9").all()
    # Ensure no slug was created
    assert len(db_slug) == 0


def test_create_family_503(client: TestClient, test_db: Session, bad_family_repo):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
        metadata={"color": "pink", "size": 0},
    )
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"


def test_create_family__invalid_geo_400(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    new_family.geography = "UK"
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The geography value UK is invalid!"


def test_create_family__invalid_category_400(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    new_family.category = "invalid"
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Invalid is not a valid FamilyCategory"


def test_create_family__invalid_org_400(client: TestClient, test_db: Session):
    _setup_db(test_db)
    new_family = create_family_dto(
        import_id="A.0.0.9",
        title="Title",
        summary="test test test",
    )
    new_family.organisation = "chicken"
    response = client.post("/api/v1/families", json=new_family.dict())
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "The organisation name chicken is invalid!"


# --- DELETE


def test_delete_family_200(
    client: TestClient, test_db: Session, admin_user_header_token
):
    _setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == 200
    n = test_db.query(Family).count()
    assert n == 2


def test_delete_family_rollback(
    client: TestClient, test_db: Session, rollback_family_repo, admin_user_header_token
):
    _setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.2", headers=admin_user_header_token
    )
    assert response.status_code == 503
    n = test_db.query(Family).count()
    assert n == 3


def test_delete_family_404(
    client: TestClient, test_db: Session, admin_user_header_token
):
    _setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.22", headers=admin_user_header_token
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Family not deleted: A.0.0.22"


def test_delete_family_503(
    client: TestClient, test_db: Session, bad_family_repo, admin_user_header_token
):
    _setup_db(test_db)
    response = client.delete(
        "/api/v1/families/A.0.0.1", headers=admin_user_header_token
    )
    assert response.status_code == 503
    data = response.json()
    assert data["detail"] == "Bad Repo"
