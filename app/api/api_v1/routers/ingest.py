from fastapi import APIRouter, Request, status

ingest_router = r = APIRouter()


@r.post("/ingest/{new_data}", response_model=str, status_code=status.HTTP_201_CREATED)
async def ingest_data(request: Request, new_data: str) -> str:

    return "Hello world"
