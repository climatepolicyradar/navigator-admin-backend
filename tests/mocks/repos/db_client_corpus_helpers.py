from typing import Optional, cast

from db_client.functions.corpus_helpers import TaxonomyData
from pytest import MonkeyPatch


def mock_corpus_helpers_db_client(taxonomy_service, monkeypatch: MonkeyPatch, mocker):

    def mock_get_taxonomy_by_corpus_type_name(_, __) -> Optional[TaxonomyData]:
        metadata = {
            "allow_blanks": False,
            "allow_any": False,
            "allowed_values": [],
        }
        return cast(TaxonomyData, {"test": metadata, "_document": {"test": metadata}})

    monkeypatch.setattr(
        taxonomy_service,
        "get_taxonomy_by_corpus_type_name",
        mock_get_taxonomy_by_corpus_type_name,
    )
    mocker.spy(taxonomy_service, "get_taxonomy_by_corpus_type_name")
