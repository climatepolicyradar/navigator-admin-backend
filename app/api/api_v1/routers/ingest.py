from fastapi import APIRouter, Request, status

from app.model.ingest import IngestDTO

ingest_router = r = APIRouter()


@r.post("/ingest", response_model=str, status_code=status.HTTP_201_CREATED)
async def ingest_data(request: Request, new_data: IngestDTO) -> str:

    print(new_data)
    return "Hello world"
