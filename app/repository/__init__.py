import app.clients.aws.s3bucket as s3bucket_repo
import app.repository.app_user as app_user_repo
import app.repository.collection as collection_repo
import app.repository.config as config_repo
import app.repository.document as document_repo
import app.repository.event as event_repo
import app.repository.family as family_repo
import app.repository.geography as geography_repo
import app.repository.metadata as metadata_repo
import app.repository.organisation as organisation_repo
from app.repository.protocols import FamilyRepo

family_repo: FamilyRepo
