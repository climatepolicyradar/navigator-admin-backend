from pydantic import BaseModel

from app.model.general import Json


class IngestFamilyDTO(BaseModel):
    """
    A JSON representation of a family for ingest.

    Note:
     - corpus_import_id is auto populated
     - slug is auto generated
     - organisation comes from the user's organisation
    """

    import_id: str
    title: str
    summary: str
    geography: str
    category: str
    metadata: Json
    collections: list[str]
    corpus_import_id: str
