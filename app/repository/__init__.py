import app.clients.aws.s3bucket as s3bucket_repo
import app.repository.app_user as app_user_repo
import app.repository.collection as collection_repo
import app.repository.config as config_repo
import app.repository.corpus as corpus_repo
import app.repository.corpus_type as corpus_type_repo
import app.repository.document as document_repo
import app.repository.event as event_repo
import app.repository.family as family_repo  # type: ignore
import app.repository.geography as geography_repo
import app.repository.organisation as organisation_repo
from app.repository.protocols import FamilyRepo

family_repo: FamilyRepo

__all__ = (
    "s3bucket_repo",
    "app_user_repo",
    "collection_repo",
    "config_repo",
    "corpus_repo",
    "corpus_type_repo",
    "document_repo",
    "event_repo",
    "family_repo",
    "geography_repo",
    "organisation_repo",
)
