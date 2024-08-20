from typing import Optional, cast

from db_client.functions.corpus_helpers import TaxonomyData
from pytest import MonkeyPatch


def mock_corpus_helpers_db_client(
    db_client_corpus_helpers, monkeypatch: MonkeyPatch, mocker
):

    def mock_get_taxonomy_by_corpus_type_name(_, __) -> Optional[TaxonomyData]:
        print(">>>>>>>>>>> Calling mock!")
        metadata = {
            "allow_blanks": False,
            "allow_any": False,
            "allowed_values": [],
        }
        return cast(TaxonomyData, {"test": metadata, "_document": metadata})

    monkeypatch.setattr(
        db_client_corpus_helpers,
        "get_taxonomy_by_corpus_type_name",
        mock_get_taxonomy_by_corpus_type_name,
    )
    mocker.spy(db_client_corpus_helpers, "get_taxonomy_by_corpus_type_name")
