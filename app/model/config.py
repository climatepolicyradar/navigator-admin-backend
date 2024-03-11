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


class ConfigReadDTO(BaseModel):
    """Definition of the new Config which just includes taxonomy."""

    geographies: Sequence[dict]
    taxonomies: Mapping[str, TaxonomyData]
    languages: Mapping[str, str]
    document: DocumentConfig
    event: EventConfig
