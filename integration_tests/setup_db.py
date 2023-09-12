from typing import cast
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models.app.users import Organisation
from app.db.models.law_policy.collection import (
    Collection,
    CollectionFamily,
    CollectionOrganisation,
)
from app.db.models.law_policy.family import Family, FamilyCategory, FamilyOrganisation
from app.db.models.law_policy.metadata import (
    FamilyMetadata,
    MetadataOrganisation,
    MetadataTaxonomy,
)


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
        "collections": ["C.0.0.2"],
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
        "collections": ["C.0.0.2"],
    },
]


EXPECTED_COLLECTIONS = [
    {
        "import_id": "C.0.0.1",
        "title": "Collection 1",
        "description": "description one",
        "families": [],
        "organisation": "test_org",
    },
    {
        "import_id": "C.0.0.2",
        "title": "Collection 2",
        "description": "description two",
        "families": ["A.0.0.1", "A.0.0.3"],
        "organisation": "test_org",
    },
]


def setup_db(test_db: Session):
    with open("integration_tests/default-data.sql") as file:
        query = text(file.read())
        test_db.execute(query)

    org_id = _setup_organisation(test_db)

    _setup_family_data(test_db, org_id)
    test_db.commit()

    _setup_collection_data(test_db, org_id)
    test_db.commit()


def _setup_organisation(test_db: Session) -> int:
    # Now an organisation
    org = Organisation(
        name="test_org",
        description="for testing",
        organisation_type="test organisation",
    )
    test_db.add(org)
    test_db.flush()
    return cast(int, org.id)


def _setup_collection_data(test_db: Session, org_id: int):
    test_db.add(
        Collection(
            import_id="C.0.0.1", title="Collection 1", description="description one"
        )
    )

    test_db.add(
        Collection(
            import_id="C.0.0.2", title="Collection 2", description="description two"
        )
    )

    test_db.add(
        CollectionOrganisation(collection_import_id="C.0.0.1", organisation_id=org_id)
    )

    test_db.add(
        CollectionOrganisation(collection_import_id="C.0.0.2", organisation_id=org_id)
    )

    test_db.add(
        CollectionFamily(collection_import_id="C.0.0.2", family_import_id="A.0.0.1")
    )

    test_db.add(
        CollectionFamily(collection_import_id="C.0.0.2", family_import_id="A.0.0.3")
    )


def _setup_family_data(test_db: Session, org_id: int):
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

    # Link the families to the org
    test_db.add(FamilyOrganisation(family_import_id="A.0.0.1", organisation_id=org_id))
    test_db.add(FamilyOrganisation(family_import_id="A.0.0.2", organisation_id=org_id))
    test_db.add(FamilyOrganisation(family_import_id="A.0.0.3", organisation_id=org_id))

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
    mo = MetadataOrganisation(taxonomy_id=tax.id, organisation_id=org_id)
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
