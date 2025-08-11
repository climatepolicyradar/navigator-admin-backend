from datetime import datetime, timedelta, timezone
from typing import Any, Optional, TypedDict, cast

from db_client.models.dfce.collection import (
    Collection,
    CollectionFamily,
    CollectionOrganisation,
)
from db_client.models.dfce.family import (
    EventStatus,
    Family,
    FamilyCorpus,
    FamilyDocument,
    FamilyEvent,
    FamilyGeography,
    Geography,
    Slug,
)
from db_client.models.dfce.metadata import FamilyMetadata
from db_client.models.document.physical_document import (
    LanguageSource,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from db_client.models.organisation import Corpus, EntityCounter
from db_client.models.organisation.users import AppUser, Organisation, OrganisationUser
from sqlalchemy import update
from sqlalchemy.orm import Session


class DBEntry(TypedDict):
    import_id: str
    title: str
    summary: str
    geography: str
    geographies: list[str]
    category: str
    status: str
    metadata: dict
    organisation: str
    corpus_import_id: str
    corpus_title: str
    corpus_type: str
    slug: str
    events: list[str]
    published_date: str | None
    last_updated_date: str | None
    documents: list[str]
    collections: list[str]
    concepts: Optional[list[dict[str, Any]]]


EXPECTED_FAMILIES: list[DBEntry] = [
    {
        "import_id": "A.0.0.1",
        "title": "apple",
        "summary": "",
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
        "slug": "Slug1",
        "events": ["E.0.0.1", "E.0.0.2"],
        "published_date": "2018-12-24T04:59:31Z",
        "last_updated_date": "2020-12-24T04:59:31Z",
        "documents": [],
        "collections": ["C.0.0.2"],
        "concepts": [],
    },
    {
        "import_id": "A.0.0.2",
        "title": "apple orange banana",
        "summary": "apple",
        "geography": "ZWE",
        "geographies": ["ZWE"],
        "category": "UNFCCC",
        "status": "Created",
        "metadata": {
            "topic": ["Mitigation"],
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
        "slug": "Slug2",
        "events": [],
        "published_date": None,
        "last_updated_date": None,
        "documents": ["D.0.0.3"],
        "collections": ["C.0.0.2"],
        "concepts": [],
    },
    {
        "import_id": "A.0.0.3",
        "title": "title",
        "summary": "orange peas",
        "geography": "AFG",
        "geographies": ["AFG"],
        "category": "UNFCCC",
        "status": "Created",
        "metadata": {"author": ["CPR"], "author_type": ["Party"]},
        "organisation": "UNFCCC",
        "corpus_import_id": "UNFCCC.corpus.i00000001.n0000",
        "corpus_title": "UNFCCC Submissions",
        "corpus_type": "Intl. agreements",
        "slug": "Slug3",
        "events": ["E.0.0.3", "E.0.0.4"],
        "published_date": "2018-12-24T04:59:33Z",
        "last_updated_date": "2018-12-24T04:59:33Z",
        "documents": ["D.0.0.1", "D.0.0.2"],
        "collections": ["C.0.0.4"],
        "concepts": [],
    },
]
EXPECTED_NUM_FAMILIES = len(EXPECTED_FAMILIES)

EXPECTED_COLLECTIONS = [
    {
        "import_id": "C.0.0.1",
        "title": "Collection 1 a very big collection",
        "description": "description one",
        "metadata": {"key": "value"},
        "families": [],
        "organisation": "Another org",
        "slug": "collection-slug-1",
    },
    {
        "import_id": "C.0.0.2",
        "title": "Collection 2",
        "description": "description two",
        "metadata": {"key": "value"},
        "families": ["A.0.0.1", "A.0.0.2"],
        "organisation": "CCLW",
        "slug": "collection-slug-2",
    },
    {
        "import_id": "C.0.0.3",
        "title": "Collection 3",
        "description": "description three",
        "metadata": {"key": "value"},
        "families": [],
        "organisation": "CCLW",
        "slug": "collection-slug-3",
    },
    {
        "import_id": "C.0.0.4",
        "title": "Collection 4",
        "description": "description four",
        "metadata": {"key": "value"},
        "families": ["A.0.0.3"],
        "organisation": "UNFCCC",
        "slug": "collection-slug-4",
    },
]
EXPECTED_NUM_COLLECTIONS = len(EXPECTED_COLLECTIONS)


EXPECTED_DOCUMENTS = [
    {
        "import_id": "D.0.0.1",
        "family_import_id": "A.0.0.3",
        "corpus_type": "Intl. agreements",
        "variant_name": "Original Language",
        "status": "Created",
        "metadata": {"role": ["MAIN"], "type": ["Law"]},
        "slug": "",
        "title": "big title1",
        "md5_sum": "sum1",
        "cdn_object": "obj1",
        "source_url": "http://source1/",
        "content_type": "application/pdf",
        "user_language_name": "English",
        "calc_language_name": "Spanish",
    },
    {
        "import_id": "D.0.0.2",
        "family_import_id": "A.0.0.3",
        "corpus_type": "Intl. agreements",
        "variant_name": "Original Language",
        "status": "Created",
        "metadata": {"role": ["MAIN"], "type": ["Law"]},
        "slug": "",
        "title": "title2",
        "md5_sum": "sum2",
        "cdn_object": "obj2",
        "source_url": "http://source2/",
        "content_type": "application/pdf",
        "user_language_name": None,
        "calc_language_name": None,
    },
    {
        "import_id": "D.0.0.3",
        "family_import_id": "A.0.0.2",
        "corpus_type": "Laws and Policies",
        "variant_name": "Original Language",
        "status": "Created",
        "metadata": {"role": ["MAIN"], "type": ["Law"]},
        "slug": "",
        "title": "title3",
        "md5_sum": "sum3",
        "cdn_object": "obj3",
        "source_url": "http://source3/",
        "content_type": "application/pdf",
        "user_language_name": None,
        "calc_language_name": None,
    },
]
EXPECTED_NUM_DOCUMENTS = len(EXPECTED_DOCUMENTS)


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
    {
        "import_id": "E.0.0.4",
        "event_title": "Future Event",
        "date": (datetime.now(tz=timezone.utc) + timedelta(days=365))
        .isoformat()
        .replace("+00:00", "Z"),
        "event_type_value": "Completed",
        "family_import_id": "A.0.0.3",
        "family_document_import_id": None,
        "event_status": EventStatus.OK,
    },
]
EXPECTED_NUM_EVENTS = len(EXPECTED_EVENTS)

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

EXPECTED_NUM_CORPORA = 2
EXPECTED_CCLW_CORPUS = {
    "import_id": "CCLW.corpus.i00000001.n0000",
    "title": "CCLW national policies",
    "description": "CCLW national policies",
    "corpus_text": (
        "\n        <p>\n          The summary of this document was written by "
        'researchers at the <a href="http://lse.ac.uk/grantham" target="_blank"> '
        "Grantham Research Institute </a> . \n          If you want to use this summary"
        ', please check <a href="'
        'https://www.lse.ac.uk/granthaminstitute/cclw-terms-and-conditions" target='
        '"_blank"> terms of use </a> for citation and licensing of third party data.'
        "\n        </p>\n"
    ),
    "corpus_image_url": "corpora/CCLW.corpus.i00000001.n0000/logo.png",
    "organisation_name": "CCLW",
    "corpus_type_name": "Laws and Policies",
    "corpus_type_description": "Laws and policies",
}
EXPECTED_UNFCCC_CORPUS = {
    "import_id": "UNFCCC.corpus.i00000001.n0000",
    "title": "UNFCCC Submissions",
    "description": "UNFCCC Submissions",
    "corpus_text": (
        "\n        <p>\n          This document was downloaded from "
        'the <a href="https://unfccc.int/" target="_blank"> UNFCCC website </a> . '
        '\n          Please check <a href="https://unfccc.int/this-site/terms-of-use'
        '" target="_blank"> terms of use </a> for citation and licensing of third '
        "party data.\n        </p>\n"
    ),
    "corpus_image_url": None,
    "organisation_name": "UNFCCC",
    "corpus_type_name": "Intl. agreements",
    "corpus_type_description": "Intl. agreements",
}
EXPECTED_CORPORA_KEYS = [
    "import_id",
    "title",
    "description",
    "corpus_text",
    "corpus_image_url",
    "organisation_id",
    "organisation_name",
    "corpus_type_name",
    "corpus_type_description",
    "metadata",
]

EXPECTED_NUM_ORGS = 3
EXPECTED_CCLW_ORG = {
    "id": 1,
    "internal_name": "CCLW",
    "display_name": "CCLW",
    "description": "LSE CCLW team",
    "type": "Academic",
    "attribution_url": None,
}
EXPECTED_UNFCCC_ORG = {
    "id": 2,
    "internal_name": "UNFCCC",
    "display_name": "UNFCCC",
    "description": "United Nations Framework Convention on Climate Change",
    "type": "UN",
    "attribution_url": None,
}


def add_data(test_db: Session, data: list[DBEntry]):
    org_id = test_db.query(Organisation).filter(Organisation.name == "CCLW").one().id
    other_org_id = (
        test_db.query(Organisation).filter(Organisation.name == "UNFCCC").one().id
    )
    _setup_family_data(test_db, org_id, other_org_id, data)
    test_db.commit()


def setup_db(test_db: Session, configure_empty: bool = False):
    setup_test_data(test_db, configure_empty)


def setup_test_data(test_db: Session, configure_empty: bool = False):
    org_id, other_org_id = _setup_organisation(test_db)

    assert test_db.query(Family).count() == 0
    _setup_family_data(test_db, org_id, other_org_id)
    test_db.commit()

    assert test_db.query(Collection).count() == 0
    _setup_collection_data(test_db, configure_empty)
    test_db.commit()

    assert test_db.query(FamilyDocument).count() == 0
    _setup_document_data(test_db)
    test_db.commit()

    assert test_db.query(FamilyEvent).count() == 0
    _setup_event_data(test_db)
    test_db.commit()

    setup_corpus(test_db)


def _add_app_user(
    test_db: Session,
    email: str,
    name: str,
    org_id,
    hashed_pass: str = "",
    is_active: bool = True,
    is_super: bool = False,
    is_admin: bool = False,
):
    test_db.add(
        AppUser(
            email=email, name=name, hashed_password=hashed_pass, is_superuser=is_super
        )
    )
    test_db.flush()
    test_db.add(
        OrganisationUser(
            appuser_email=email,
            organisation_id=org_id,
            job_title="",
            is_active=is_active,
            is_admin=is_admin,
        )
    )
    test_db.commit()


def _get_org_id_from_name(test_db: Session, name: str) -> int:
    return test_db.query(Organisation.id).filter(Organisation.name == name).scalar()


def _setup_organisation(test_db: Session) -> tuple[int, int]:
    # Now an organisation
    cclw = test_db.query(Organisation).filter(Organisation.name == "CCLW").one()
    unfccc = test_db.query(Organisation).filter(Organisation.name == "UNFCCC").one()

    another_org = Organisation(
        name="Another org",
        description="because we will have more than one org",
        organisation_type="test",
        display_name="Another org",
    )
    test_db.add(another_org)
    test_db.flush()

    # Also link to the test users
    _add_app_user(
        test_db,
        "cclw@cpr.org",
        "CCLWTestUser",
        cclw.id,
        "$2b$12$XXMr7xoEY2fzNiMR3hq.PeJBUUchJyiTfJP.Rt2eq9hsPzt9SXzFC",
        is_admin=False,
    )
    _add_app_user(
        test_db,
        "unfccc@cpr.org",
        "UNFCCCTestUser",
        unfccc.id,
        "$2b$12$XXMr7xoEY2fzNiMR3hq.PeJBUUchJyiTfJP.Rt2eq9hsPzt9SXzFC",
        is_admin=False,
    )
    _add_app_user(
        test_db,
        "another@cpr.org",
        "AnotherTestUser",
        another_org.id,
        "$2b$12$XXMr7xoEY2fzNiMR3hq.PeJBUUchJyiTfJP.Rt2eq9hsPzt9SXzFC",
    )
    _add_app_user(
        test_db,
        "test1@cpr.org",
        "TestInactive",
        cclw.id,
        hashed_pass="$2b$12$q.UbWEdeibUuApI2QDbmQeG5WmAPfNmooG1cAoCWjyJXvgiAVVdlK",
        is_active=False,
    )
    _add_app_user(
        test_db, "test2@cpr.org", "TestHashedPassEmpty", cclw.id, hashed_pass=""
    )
    _add_app_user(
        test_db,
        "test3@cpr.org",
        "TestPassMismatch",
        cclw.id,
        hashed_pass="$2b$12$WZq1rRMvU.Tv1VutLw.rju/Ez5ETkYqP3KufdcSFJm3GTRZP8E52C",
    )
    _add_app_user(
        test_db,
        "non-admin@cpr.org",
        "Admin",
        cclw.id,
        hashed_pass="$2b$12$XXMr7xoEY2fzNiMR3hq.PeJBUUchJyiTfJP.Rt2eq9hsPzt9SXzFC",
    )
    _add_app_user(
        test_db,
        "non-admin-super@cpr.org",
        "Super",
        cclw.id,
        hashed_pass="$2b$12$XXMr7xoEY2fzNiMR3hq.PeJBUUchJyiTfJP.Rt2eq9hsPzt9SXzFC",
        is_super=True,
    )
    _add_app_user(
        test_db,
        "admin@cpr.org",
        "Admin",
        cclw.id,
        hashed_pass="$2b$12$XXMr7xoEY2fzNiMR3hq.PeJBUUchJyiTfJP.Rt2eq9hsPzt9SXzFC",
        is_admin=True,
    )
    _add_app_user(
        test_db,
        "super@cpr.org",
        "Super",
        cclw.id,
        hashed_pass="$2b$12$XXMr7xoEY2fzNiMR3hq.PeJBUUchJyiTfJP.Rt2eq9hsPzt9SXzFC",
        is_super=True,
    )

    return cast(int, cclw.id), cast(int, another_org.id)


def setup_corpus(test_db: Session) -> None:
    test_db.execute(
        update(EntityCounter).values(
            counter=1,
        )
    )
    test_db.commit()

    for item in test_db.query(EntityCounter.counter).all():
        assert item[0] == 1


def _setup_collection_data(
    test_db: Session,
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
                valid_metadata=data["metadata"],
            )
        )

        test_db.add(
            CollectionOrganisation(
                collection_import_id=data["import_id"],
                organisation_id=_get_org_id_from_name(test_db, data["organisation"]),
            )
        )
        test_db.add(
            Slug(
                name=data["slug"],
                collection_import_id=data["import_id"],
            )
        )

    for collection in EXPECTED_COLLECTIONS:
        collection_families = collection["families"]
        for family_import_id in collection_families:
            test_db.add(
                CollectionFamily(
                    collection_import_id=collection["import_id"],
                    family_import_id=family_import_id,
                )
            )


def _setup_family_data(
    test_db: Session,
    default_org_id: int,
    other_org_id: int,
    initial_data: list[DBEntry] = EXPECTED_FAMILIES,
    configure_empty: bool = False,
) -> None:
    if configure_empty is True:
        return None

    num_families = len(initial_data)
    for index in range(num_families):
        data = initial_data[index]
        geographies = (
            test_db.query(Geography).filter(Geography.value.in_(data["geographies"]))
        ).all()

        test_db.add(
            Family(
                import_id=data["import_id"],
                title=data["title"],
                description=data["summary"],
                family_category=data["category"],
            )
        )
        family_geographies = [
            FamilyGeography(
                family_import_id=data["import_id"], geography_id=geography.id
            )
            for geography in geographies
        ]
        test_db.add_all(family_geographies)

        corpus = (
            test_db.query(Corpus)
            .filter(
                Corpus.organisation_id
                == _get_org_id_from_name(test_db, data["organisation"])
            )
            .one()
        )

        # Link the families to the corpus
        test_db.add(
            FamilyCorpus(
                family_import_id=data["import_id"],
                corpus_import_id=corpus.import_id,
            )
        )

    # Now add the metadata onto the families
    for index in range(num_families):
        data = initial_data[index]
        test_db.add(
            FamilyMetadata(
                family_import_id=data["import_id"],
                value=data["metadata"],
            )
        )
        test_db.add(
            Slug(
                name=data["slug"],
                family_import_id=data["import_id"],
            )
        )


def _setup_document_data(test_db: Session, configure_empty: bool = False) -> None:
    if configure_empty is True:
        return None

    family_ids = [f["import_id"] for f in EXPECTED_FAMILIES]

    phys_docs = []
    for _, data in enumerate(EXPECTED_DOCUMENTS):
        for family_id in family_ids:
            if family_id != data["family_import_id"]:
                continue

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
                valid_metadata=data["metadata"],
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
            valid_metadata={
                "event_type": [data["event_type_value"]],
                "datetime_event_name": ["Passed/Approved"],  # TODO: Fix in PDCT-1622
            },
        )
        test_db.add(fe)
        test_db.flush()
