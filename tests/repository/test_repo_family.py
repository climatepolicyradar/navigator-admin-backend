"""Tests for the family repo TODO: When using a database this will need a fixture."""

from app.model.family import FamilyDTO


def test_get_family_returns_family(family_repo):
    result: FamilyDTO = family_repo.get_family("sample1")
    assert result is not None
    # TODO: Check all fields
    assert len(result.collections) == 2


def test_get_family_returns_none(family_repo):
    result = family_repo.get_family("sample9")
    assert result is None


def test_get_all_families_returns_correct(family_repo):
    result = family_repo.get_all_families()
    assert len(result) == 2


def test_search_families(family_repo):
    result = family_repo.search_families("two")
    assert len(result) == 1
    assert result[0].import_id == "sample2"


def test_delete_family(family_repo):
    ok = family_repo.delete_family("sample1")
    assert ok
    result = family_repo.get_all_families()
    assert len(result) == 1
    assert result[0].import_id == "sample2"


def test_delete_family_when_missing(family_repo):
    ok = family_repo.delete_family("sample9")
    assert not ok


def test_update_family(family_repo):
    family = family_repo.get_family("sample1")
    assert family is not None
    family.slug = "snail"

    result = family_repo.update_family("sample1", family)
    assert result is not None
    assert result.slug == "snail"

    # Also re-check getting the family again
    new_family = family_repo.get_family("sample1")
    assert new_family.slug == "snail"


def test_update_family_when_missing(family_repo):
    family = family_repo.get_family("sample1")
    assert family is not None
    new_family = family_repo.update_family("sample9", family)
    assert new_family is None


def test_create_family(family_repo):
    new_family = FamilyDTO(
        import_id="test",
        title="This is a test",
        summary="summary",
        geography="geo",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )
    family = family_repo.create_family(new_family)
    assert family is not None

    # Also re-check getting the family again
    new_family = family_repo.get_family("test")
    assert new_family.title == "This is a test"


def test_create_family_when_preexisting(family_repo):
    new_family = FamilyDTO(
        import_id="sample1",
        title="This is a test",
        summary="summary",
        geography="geo",
        category="category",
        status="status",
        metadata={},
        slug="slug",
        events=["e1", "e2"],
        published_date=None,
        last_updated_date=None,
        documents=["doc1", "doc2"],
        collections=["col1", "col2"],
    )
    result = family_repo.create_family(new_family)
    assert result is None
