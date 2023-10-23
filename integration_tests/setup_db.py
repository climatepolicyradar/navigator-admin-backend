from typing import cast
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.clients.db.models.app.users import Organisation
from app.clients.db.models.document.physical_document import (
    LanguageSource,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from app.clients.db.models.law_policy.collection import (
    Collection,
    CollectionFamily,
    CollectionOrganisation,
)
from app.clients.db.models.law_policy.family import (
    EventStatus,
    Family,
    FamilyDocument,
    FamilyEvent,
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
        "organisation": "CCLW",
        "slug": "Slug1",
        "events": ["E.0.0.1", "E.0.0.2"],
        "published_date": "2018-12-24T04:59:31Z",
        "last_updated_date": "2020-12-24T04:59:31Z",
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
        "organisation": "CCLW",
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
        "organisation": "CCLW",
        "slug": "Slug3",
        "events": ["E.0.0.3"],
        "published_date": "2018-12-24T04:59:33Z",
        "last_updated_date": "2018-12-24T04:59:33Z",
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
        "organisation": "CCLW",
    },
    {
        "import_id": "C.0.0.2",
        "title": "Collection 2",
        "description": "description two",
        "families": ["A.0.0.1", "A.0.0.3"],
        "organisation": "CCLW",
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
        "user_language_name": "English",
        "calc_language_name": "Spanish",
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
        "user_language_name": None,
        "calc_language_name": None,
    },
]

EXPECTED_NUM_EVENTS = 3
EXPECTED_EVENTS = [
    {
        "import_id": "E.0.0.1",
        "event_title": "bananas title1",
        "date": "2018-12-24T04:59:31Z",
        "event_type_value": "Passed/Approved",
        "family_import_id": "A.0.0.1",
        "family_document_import_id": None,
        "event_status": EventStatus.OK,
    },
    {
        "import_id": "E.0.0.2",
        "event_title": "cabbages title2",
        "date": "2020-12-24T04:59:31Z",
        "event_type_value": "Amended",
        "family_import_id": "A.0.0.1",
        "family_document_import_id": None,
        "event_status": EventStatus.OK,
    },
    {
        "import_id": "E.0.0.3",
        "event_title": "cabbages title3",
        "date": "2018-12-24T04:59:33Z",
        "event_type_value": "Amended",
        "family_import_id": "A.0.0.3",
        "family_document_import_id": None,
        "event_status": EventStatus.OK,
    },
]

EXPECTED_ANALYTICS_SUMMARY_KEYS = [
    "n_documents",
    "n_families",
    "n_collections",
    "n_events",
]
EXPECTED_ANALYTICS_SUMMARY = {
    "n_documents": EXPECTED_NUM_DOCUMENTS,
    "n_families": EXPECTED_NUM_FAMILIES,
    "n_collections": EXPECTED_NUM_COLLECTIONS,
    "n_events": EXPECTED_NUM_EVENTS,
}


def setup_db(test_db: Session, configure_empty: bool = False):
    with open("integration_tests/default-data.sql") as file:
        query = text(file.read())
        test_db.execute(query)

    setup_test_data(test_db, configure_empty)


def setup_test_data(test_db: Session, configure_empty: bool = False):
    org_id = _setup_organisation(test_db)

    _setup_family_data(test_db, org_id)
    test_db.commit()

    _setup_collection_data(test_db, org_id, configure_empty)
    test_db.commit()

    _setup_document_data(test_db, "A.0.0.3")
    test_db.commit()

    _setup_event_data(test_db, "A.0.0.3")
    test_db.commit()


def _setup_organisation(test_db: Session) -> int:
    # Now an organisation
    org = Organisation(
        name="CCLW",
        description="for testing",
        organisation_type="test organisation",
    )
    test_db.add(org)
    test_db.add(
        Organisation(
            name="Another org",
            description="because we will have more than one org",
            organisation_type="test",
        )
    )
    test_db.flush()
    return cast(int, org.id)


def _setup_collection_data(
    test_db: Session,
    org_id: int,
    configure_empty: bool = False,
) -> None:
    if configure_empty is True:
        return None

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


def _setup_family_data(
    test_db: Session,
    org_id: int,
    configure_empty: bool = False,
) -> None:
    if configure_empty is True:
        return None

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


def _setup_document_data(
    test_db: Session,
    family_id: str,
    configure_empty: bool = False,
) -> None:
    if configure_empty is True:
        return None

    phys_docs = []
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
        phys_docs.append(pd.id)

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

    # Setup english as user language for first document
    test_db.add(
        PhysicalDocumentLanguage(
            language_id=1826, document_id=phys_docs[0], source=LanguageSource.USER
        )
    )
    test_db.add(
        PhysicalDocumentLanguage(
            language_id=5991, document_id=phys_docs[0], source=LanguageSource.MODEL
        )
    )
    test_db.flush()


def _setup_event_data(
    test_db: Session,
    family_id: str,
    configure_empty: bool = False,
) -> None:
    """
    TODO: Need to test events associated with family documents.

    family_document_import_id=data["family_document_import_id"],
    """
    if configure_empty is True:
        return None

    for index in range(EXPECTED_NUM_EVENTS):
        data = EXPECTED_EVENTS[index]
        fe = FamilyEvent(
            import_id=data["import_id"],
            title=data["event_title"],
            date=data["date"],
            event_type_name=data["event_type_value"],
            family_import_id=data["family_import_id"],
            status=data["event_status"],
        )
        test_db.add(fe)
        test_db.flush()
