from typing import Optional, Sequence, cast

from db_client.functions.corpus_helpers import TaxonomyData
from pytest import MonkeyPatch
from sqlalchemy import exc


def mock_metadata_db_client(db_client_metadata, monkeypatch: MonkeyPatch, mocker):
    db_client_metadata.return_empty = False
    db_client_metadata.throw_repository_error = False
    db_client_metadata.error = False
    db_client_metadata.valid = True
    db_client_metadata.bad_taxonomy = False

    def maybe_throw():
        if db_client_metadata.throw_repository_error:
            raise exc.SQLAlchemyError("")

    def mock_validate_metadata(_) -> Optional[Sequence[str]]:
        maybe_throw()
        if db_client_metadata.return_empty:
            raise TypeError

        return []

    def mock_get_taxonomy_from_corpus(_, __) -> Optional[TaxonomyData]:
        if db_client_metadata.bad_taxonomy:
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
        db_client_metadata, "get_taxonomy_from_corpus", mock_get_taxonomy_from_corpus
    )
    mocker.spy(db_client_metadata, "get_taxonomy_from_corpus")

    monkeypatch.setattr(
        db_client_metadata,
        "get_entity_specific_taxonomy",
        mock_get_entity_specific_taxonomy,
    )
    mocker.spy(db_client_metadata, "get_entity_specific_taxonomy")
