from typing import Optional, Sequence, cast

from db_client.functions.corpus_helpers import TaxonomyData
from pytest import MonkeyPatch
from sqlalchemy import exc


def mock_metadata_db_client(metadata_repo, monkeypatch: MonkeyPatch, mocker):
    metadata_repo.return_empty = False
    metadata_repo.throw_repository_error = False
    metadata_repo.error = False
    metadata_repo.valid = True
    metadata_repo.bad_taxonomy = False

    def maybe_throw():
        if metadata_repo.throw_repository_error:
            raise exc.SQLAlchemyError("")

    def mock_validate_metadata(_) -> Optional[Sequence[str]]:
        maybe_throw()
        if metadata_repo.return_empty:
            raise TypeError

        return []

    def mock_get_taxonomy_from_corpus(_, __) -> Optional[TaxonomyData]:
        if metadata_repo.bad_taxonomy:
            return None

        color = {
            "allow_blanks": False,
            "allow_any": False,
            "allowed_values": ["pink", "blue"],
        }
        size = {"allow_blanks": True, "allow_any": True, "allowed_values": []}
        return cast(TaxonomyData, {"color": color, "size": size})

    def mock_get_entity_specific_taxonomy(_, entity_key=None) -> Optional[TaxonomyData]:
        color = {
            "allow_blanks": False,
            "allow_any": False,
            "allowed_values": ["pink", "blue"],
        }
        if entity_key is not None:
            color_tax = {"color": color}
            return cast(TaxonomyData, color_tax)
        size = {"allow_blanks": True, "allow_any": True, "allowed_values": []}
        return cast(TaxonomyData, {"color": color, "size": size})

    monkeypatch.setattr(
        metadata_repo, "get_taxonomy_from_corpus", mock_get_taxonomy_from_corpus
    )
    mocker.spy(metadata_repo, "get_taxonomy_from_corpus")

    monkeypatch.setattr(
        metadata_repo, "get_entity_specific_taxonomy", mock_get_entity_specific_taxonomy
    )
    mocker.spy(metadata_repo, "get_entity_specific_taxonomy")

    # monkeypatch.setattr(metadata_repo, "validate_metadata", mock_validate_metadata)
    # mocker.spy(metadata_repo, "validate_metadata")
