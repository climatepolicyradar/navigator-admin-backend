import pytest

from app.errors import ValidationError
from app.service.validation import validate_entity_relationships


def test_validate_entity_relationships_when_no_family_matching_document():
    fam_import_id = "test.new.family.0"
    test_data = {
        "documents": [
            {"import_id": "test.new.document.0", "family_import_id": fam_import_id}
        ]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"No entity with id {fam_import_id} found" == e.value.message


def test_validate_entity_relationships_when_no_family_matching_event():
    fam_import_id = "test.new.family.0"
    test_data = {
        "events": [{"import_id": "test.new.event.0", "family_import_id": fam_import_id}]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"No entity with id {fam_import_id} found" == e.value.message


def test_validate_entity_relationships_when_no_collection_matching_family():
    coll_import_id = "test.new.collection.0"
    test_data = {
        "families": [{"import_id": "test.new.event.0", "collections": [coll_import_id]}]
    }

    with pytest.raises(ValidationError) as e:
        validate_entity_relationships(test_data)
    assert f"No entity with id {coll_import_id} found" == e.value.message
