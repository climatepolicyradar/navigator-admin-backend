from fastapi import APIRouter, Request, status
from pydantic import BaseModel

ingest_router = r = APIRouter()


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


@r.post("/ingest", response_model=str, status_code=status.HTTP_201_CREATED)
async def ingest_data(request: Request, new_data: IngestDTO) -> str:

    print(new_data)
    return "Hello world"
