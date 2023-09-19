from typing import Optional, Tuple
from app.clients.aws.client import get_s3_client
from app.model.document import DocumentDTO
import app.repository.document_file as document_repo


def get_upload_details(filename: str, overwrite: Optional[bool]) -> Tuple[str, str]:
    client = get_s3_client()

    # TODO : Check if file pre-exists so we can use "overwrite"
    return document_repo.get_upload_details(client, filename)


def create(doc: DocumentDTO):
    return doc
