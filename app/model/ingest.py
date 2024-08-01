from pydantic import BaseModel


class DocumentIngestDTO(BaseModel):
    metadata: list[str]
    events: list[str]


class FamilyIngestDTO(BaseModel):
    name: str
    summary: str
    metadata: list[str]
    events: list[str]
    documents: list[DocumentIngestDTO]


class IngestDTO(BaseModel):
    corpus_id: str
    families: list[FamilyIngestDTO]
