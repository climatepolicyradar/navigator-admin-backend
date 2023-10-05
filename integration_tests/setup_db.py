from typing import cast
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.clients.db.models.app.users import Organisation
from app.clients.db.models.document.physical_document import PhysicalDocument
from app.clients.db.models.law_policy.collection import (
    Collection,
    CollectionFamily,
    CollectionOrganisation,
)
from app.clients.db.models.law_policy.family import (
    Family,
    FamilyDocument,
    FamilyOrganisation,
    Slug,
)
from app.clients.db.models.law_policy.metadata import (
    FamilyMetadata,
    MetadataOrganisation,
    MetadataTaxonomy,
)

# TODO: Change this to use the service.family.create - so we don't miss anything here
EXPECTED_NUM_FAMILIES = 3
EXPECTED_FAMILIES = [
    {
        "import_id": "A.0.0.1",
        "title": "apple",
        "summary": "",
        "geography": "South Asia",
        "category": "UNFCCC",
        "status": "Created",
        "metadata": {"size": [3], "color": ["red"]},
        "organisation": "test_org",
        "slug": "Slug1",
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
        "metadata": {"size": [4], "color": ["green"]},
        "organisation": "test_org",
        "slug": "Slug2",
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
        "metadata": {"size": [100], "color": ["blue"]},
        "organisation": "test_org",
        "slug": "Slug3",
        "events": [],
        "published_date": None,
        "last_updated_date": None,
        "documents": ["D.0.0.1", "D.0.0.2"],
        "collections": ["C.0.0.2"],
    },
]


EXPECTED_NUM_COLLECTIONS = 2
EXPECTED_COLLECTIONS = [
    {
        "import_id": "C.0.0.1",
        "title": "Collection 1 a very big collection",
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

EXPECTED_NUM_DOCUMENTS = 2
EXPECTED_DOCUMENTS = [
    {
        "import_id": "D.0.0.1",
        "family_import_id": "A.0.0.3",
        "variant_name": "Original Language",
        "status": "Created",
        "role": "MAIN",
        "type": "Law",
        "slug": "",
        "physical_id": 1,
        "title": "big title1",
        "md5_sum": "sum1",
        "cdn_object": "obj1",
        "source_url": "source1",
        "content_type": "application/pdf",
        "user_language_name": "TODO",
    },
    {
        "import_id": "D.0.0.2",
        "family_import_id": "A.0.0.3",
        "variant_name": "Original Language",
        "status": "Created",
        "role": "MAIN",
        "type": "Law",
        "slug": "",
        "physical_id": 2,
        "title": "title2",
        "md5_sum": "sum2",
        "cdn_object": "obj2",
        "source_url": "source2",
        "content_type": "application/pdf",
        "user_language_name": "TODO",
    },
]

EXPECTED_ANALYTICS_SUMMARY_KEYS = ["n_documents", "n_families", "n_collections", "n_events"]
EXPECTED_ANALYTICS_SUMMARY = {
    "n_documents": EXPECTED_NUM_DOCUMENTS,
    "n_families": EXPECTED_NUM_FAMILIES,
    "n_collections": EXPECTED_NUM_COLLECTIONS,
    "n_events": 0,
}


def setup_db(test_db: Session):
    with open("integration_tests/default-data.sql") as file:
        query = text(file.read())
        test_db.execute(query)

    org_id = _setup_organisation(test_db)

    _setup_family_data(test_db, org_id)
    test_db.commit()

    _setup_collection_data(test_db, org_id)
    test_db.commit()

    _setup_document_data(test_db, "A.0.0.3")
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
    for index in range(EXPECTED_NUM_COLLECTIONS):
        data = EXPECTED_COLLECTIONS[index]
        test_db.add(
            Collection(
                import_id=data["import_id"],
                title=data["title"],
                description=data["description"],
            )
        )

        test_db.add(
            CollectionOrganisation(
                collection_import_id=data["import_id"], organisation_id=org_id
            )
        )

    test_db.add(
        CollectionFamily(collection_import_id="C.0.0.2", family_import_id="A.0.0.1")
    )

    test_db.add(
        CollectionFamily(collection_import_id="C.0.0.2", family_import_id="A.0.0.3")
    )


def _setup_family_data(test_db: Session, org_id: int):
    for index in range(EXPECTED_NUM_FAMILIES):
        data = EXPECTED_FAMILIES[index]
        test_db.add(
            Family(
                import_id=data["import_id"],
                title=data["title"],
                description=data["summary"],
                geography_id=1,
                family_category=data["category"],
            )
        )

        # Link the families to the org
        test_db.add(
            FamilyOrganisation(
                family_import_id=data["import_id"], organisation_id=org_id
            )
        )

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
    for index in range(EXPECTED_NUM_FAMILIES):
        data = EXPECTED_FAMILIES[index]
        test_db.add(
            FamilyMetadata(
                family_import_id=data["import_id"],
                taxonomy_id=tax.id,
                value=data["metadata"],
            )
        )
        test_db.add(
            Slug(
                name=f"Slug{index+1}",
                family_import_id=data["import_id"],
            )
        )


def _setup_document_data(test_db: Session, family_id: str) -> None:
    for index in range(EXPECTED_NUM_DOCUMENTS):
        data = EXPECTED_DOCUMENTS[index]
        pd = PhysicalDocument(
            id=None,
            title=data["title"],
            md5_sum=data["md5_sum"],
            cdn_object=data["cdn_object"],
            source_url=data["source_url"],
            content_type=data["content_type"],
        )
        test_db.add(pd)
        test_db.flush()

        fd = FamilyDocument(
            family_import_id=family_id,
            physical_document_id=pd.id,
            import_id=data["import_id"],
            variant_name=data["variant_name"],
            document_status=data["status"],
            document_type=data["type"],
            document_role=data["role"],
        )
        test_db.add(fd)
        test_db.flush()
