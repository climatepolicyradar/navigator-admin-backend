from typing import Mapping, Sequence, Union

from pydantic import BaseModel

TaxonomyData = Mapping[str, Mapping[str, Union[bool, str, Sequence[str]]]]


class EventConfig(BaseModel):
    """Everything you need to know about events."""

    types: Sequence[str]


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
    taxonomy: TaxonomyData


class ConfigReadDTO(BaseModel):
    """Definition of the new Config which includes corpora."""

    geographies: Sequence[dict]
    organisations: Mapping[str, Sequence[CorpusData]]
    languages: Mapping[str, str]
    document: DocumentConfig
    event: EventConfig
