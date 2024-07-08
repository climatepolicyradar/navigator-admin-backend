from typing import Mapping, Sequence, Union

from db_client.functions.corpus_helpers import TaxonomyData
from pydantic import BaseModel


class DocumentConfig(BaseModel):
    """Everything you need to know about documents."""

    roles: Sequence[str]
    types: Sequence[str]
    variants: Sequence[str]


class CorpusData(BaseModel):
    """Contains the Corpus and CorpusType info"""

    corpus_import_id: str
    title: str
    description: str
    corpus_type: str
    corpus_type_description: str
    organisation: Mapping[str, Union[int, str]]
    taxonomy: TaxonomyData


class ConfigReadDTO(BaseModel):
    """Definition of the new Config which just includes taxonomy."""

    geographies: Sequence[dict]
    corpora: Sequence[CorpusData]
    languages: Mapping[str, str]
    document: DocumentConfig
