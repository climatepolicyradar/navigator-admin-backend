import pytest

from app.errors import ValidationError
from app.service.validation import validate_entity_relationships


def test_validate_entity_relationships_when_no_family_matching_document():
    missing_fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {
                "import_id": "test.new.document.0",
                "family_import_id": missing_fam_import_id,
            }
        ]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"Missing entities: ['{missing_fam_import_id}']" == e.value.message


def test_validate_entity_relationships_when_no_family_matching_event():
    missing_fam_import_id = "test.new.family.0"
    test_data = {
        "events": [
            {"import_id": "test.new.event.0", "family_import_id": missing_fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"Missing entities: ['{missing_fam_import_id}']" == e.value.message


def test_validate_entity_relationships_when_no_document_matching_event():
    fam_import_id = "test.new.family.0"
    missing_doc_import_id = "test.new.document.0"
    test_data = {
        "families": [{"import_id": fam_import_id, "collections": []}],
        "events": [
            {
                "import_id": "test.new.event.0",
                "family_import_id": fam_import_id,
                "family_document_import_id": missing_doc_import_id,
            }
        ],
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"Missing entities: ['{missing_doc_import_id}']" == e.value.message


def test_validate_entity_relationships_handles_no_document_import_id_on_event():
    fam_import_id = "test.new.family.0"
    test_data = {
        "families": [{"import_id": fam_import_id, "collections": []}],
        "events": [
            {
                "import_id": "test.new.event.0",
                "family_import_id": fam_import_id,
                "family_document_import_id": None,
            },
        ],
    }

    validate_entity_relationships(test_data)


def test_validate_entity_relationships_when_no_collection_matching_family():
    missing_coll_import_id = "test.new.collection.0"
    test_data = {
        "families": [
            {"import_id": "test.new.family.0", "collections": [missing_coll_import_id]}
        ]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"Missing entities: ['{missing_coll_import_id}']" == e.value.message


def test_validate_entity_relationships_includes_deduplicated_list_of_all_missing_entities_in_error_message():
    missing_coll_import_id = "test.new.collection.0"
    missing_fam_import_id = "test.new.family.1"
    test_data = {
        "families": [
            {"import_id": "test.new.family.0", "collections": [missing_coll_import_id]}
        ],
        "documents": [
            {
                "import_id": "test.new.document.0",
                "family_import_id": missing_fam_import_id,
            }
        ],
        "events": [
            {"import_id": "test.new.event.0", "family_import_id": missing_fam_import_id}
        ],
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert (
        f"Missing entities: ['{missing_coll_import_id}', '{missing_fam_import_id}']"
        == e.value.message
    )
