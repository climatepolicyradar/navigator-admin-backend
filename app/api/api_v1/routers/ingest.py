from typing import Any

from fastapi import APIRouter, Request, status

ingest_router = r = APIRouter()


@r.post("/ingest", response_model=str, status_code=status.HTTP_201_CREATED)
async def ingest_data(request: Request, new_data: dict[str, Any]) -> str:

    print(new_data)
    return "Hello world"
