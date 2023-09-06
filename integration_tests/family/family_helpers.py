from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.models.app.users import Organisation
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


def setup_db(test_db: Session):
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
