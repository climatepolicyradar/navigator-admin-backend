from typing import Tuple
import logging
from typing import Optional, cast
from sqlalchemy.orm import Session, Query
from sqlalchemy import Column
from app.clients.db.models.app.counters import CountedEntity
from app.clients.db.models.law_policy.family import (
    DocumentStatus,
    FamilyDocumentRole,
    FamilyDocumentType,
    Slug,
    Variant,
)
from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
from app.clients.db.models.document.physical_document import (
    Language,
    LanguageSource,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from app.clients.db.models.law_policy import (
    FamilyDocument,
)
from sqlalchemy.exc import NoResultFound

from sqlalchemy import or_, update as db_update
from sqlalchemy_utils import escape_like

from app.repository.helpers import generate_import_id, generate_slug
from app.repository import family as family_repo


_LOGGER = logging.getLogger(__name__)

DocumentTuple = Tuple[FamilyDocument, PhysicalDocument, Slug]
CreateObjects = Tuple[PhysicalDocumentLanguage, FamilyDocument, PhysicalDocument]


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of the query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.

    # FIXME: TODO: will this work with multiple slugs????
    return (
        db.query(FamilyDocument, PhysicalDocument, Slug)
        .filter(FamilyDocument.physical_document_id == PhysicalDocument.id)
        .join(
            Slug,
            Slug.family_document_import_id == FamilyDocument.import_id,
            isouter=True,
        )
    )


def _document_to_dto(doc_tuple: DocumentTuple) -> DocumentReadDTO:
    fd, pd, slug = doc_tuple
    return DocumentReadDTO(
        import_id=cast(str, fd.import_id),
        family_import_id=cast(str, fd.family_import_id),
        variant_name=cast(Variant, fd.variant_name),
        status=cast(DocumentStatus, fd.document_status),
        role=cast(FamilyDocumentRole, fd.document_role),
        type=cast(FamilyDocumentType, fd.document_type),
        slug=cast(str, slug.name) if slug is not None else "",
        physical_id=cast(int, pd.id),
        title=cast(str, pd.title),
        md5_sum=cast(str, pd.md5_sum),
        cdn_object=cast(str, pd.cdn_object),
        source_url=cast(str, pd.source_url),
        content_type=cast(str, pd.content_type),
        user_language_name="TODO",
    )


def _dto_to_family_document_dict(dto: DocumentCreateDTO) -> dict:
    return {
        "family_import_id": dto.family_import_id,
        "physical_document_id": 0,
        "variant_name": dto.variant_name,
        "document_type": dto.type,
        "document_role": dto.role,
    }


def _document_tuple_from_dto(db: Session, dto: DocumentCreateDTO) -> CreateObjects:
    language = PhysicalDocumentLanguage(
        language_id=db.query(Language.id)
        .filter(Language.name == dto.user_language_name)
        .scalar(),
        document_id=None,
        source=LanguageSource.USER,
        visible=True,
    )
    fam_doc = FamilyDocument(**_dto_to_family_document_dict(dto))
    phys_doc = PhysicalDocument(
        id=None,
        title=dto.title,
        source_url=dto.source_url,
    )
    return language, fam_doc, phys_doc


def all(db: Session) -> list[DocumentReadDTO]:
    """
    Returns all the documents.

    :param db Session: the database connection
    :return Optional[DocumentResponse]: All of things
    """
    doc_tuples = _get_query(db).all()

    if not doc_tuples:
        return []

    result = [_document_to_dto(d) for d in doc_tuples]

    return result


def get(db: Session, import_id: str) -> Optional[DocumentReadDTO]:
    """
    Gets a single document from the repository.

    :param db Session: the database connection
    :param str import_id: The import_id of the document
    :return Optional[DocumentResponse]: A single document or nothing
    """
    try:
        doc_tuple = _get_query(db).filter(FamilyDocument.import_id == import_id).one()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _document_to_dto(doc_tuple)


def search(db: Session, search_term: str) -> list[DocumentReadDTO]:
    """
    Gets a list of documents from the repository searching title and summary.

    :param db Session: the database connection
    :param str search_term: Any search term to filter on title or summary
    :return Optional[list[DocumentResponse]]: A list of matches
    """
    term = f"%{escape_like(search_term)}%"
    search = or_(PhysicalDocument.title.ilike(term))
    found = _get_query(db).filter(search).all()

    return [_document_to_dto(d) for d in found]


def update(db: Session, import_id: str, document: DocumentWriteDTO) -> bool:
    """
    Updates a single entry with the new values passed.

    :param db Session: the database connection
    :param str import_id: The document import id to change.
    :param DocumentDTO document: The new values
    :return bool: True if new values were set otherwise false.
    """
    # TODO: Implement this:

    new_values = document.model_dump()

    original_fd = (
        db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == import_id)
        .one_or_none()
    )

    if original_fd is None:  # Not found the document to update
        _LOGGER.error(f"Unable to find document for update {import_id}")
        return False

    original_pd = (
        db.query(PhysicalDocument)
        .filter(PhysicalDocument.id == original_fd.physical_document_id)
        .one_or_none()
    )

    if original_pd is None:  # Not found the document to update
        _LOGGER.error(
            f"Unable to find document for update {original_fd.physical_document_id}"
        )
        return False

    update_slug = original_pd.title != new_values["title"]

    commands = [
        db_update(PhysicalDocument)
        .where(PhysicalDocument.id == original_pd.id)
        .values(
            title=new_values["title"],
            source_url=new_values["source_url"],
        ),
        db_update(FamilyDocument)
        .where(FamilyDocument.import_id == original_fd.import_id)
        .values(
            variant_name=new_values["variant_name"],
            document_role=new_values["role"],
            document_type=new_values["type"],
        ),
    ]

    for c in commands:
        result = db.execute(c)

    if result.rowcount == 0:  # type: ignore
        msg = f"Could not update document fields: {document}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    if update_slug:
        db.add(
            Slug(
                family_document_import_id=original_fd.import_id,
                name=generate_slug(db, new_values["title"]),
            )
        )
    return True


def create(db: Session, document: DocumentCreateDTO) -> str:
    """
    Creates a new document.

    :param db Session: the database connection
    :param DocumentDTO document: the values for the new document
    :param int org_id: a validated organisation id
    :return str: The import id
    """
    try:
        language, family_doc, phys_doc = _document_tuple_from_dto(db, document)

        db.add(phys_doc)
        db.flush()

        # Update the FamilyDocument with the new PhysicalDocument id
        family_doc.physical_document_id = phys_doc.id

        # Add the language link with the new PhysicalDocument id
        language.document_id = phys_doc.id

        # Generate the import_id for the new document
        org = family_repo.get_organisation(db, cast(str, family_doc.family_import_id))
        if org is None:
            raise ValidationError(
                f"Cannot find counter to generate id for {family_doc.family_import_id}"
            )

        org_name = cast(str, org.name)

        family_doc.import_id = cast(
            Column, generate_import_id(db, CountedEntity.Document, org_name)
        )

        # Add the new document and its language link
        db.add(family_doc)
        db.add(language)
        db.flush()

        # Finally the slug
        db.add(
            Slug(
                family_document_import_id=family_doc.import_id,
                name=generate_slug(db, document.title),
            )
        )
    except Exception as e:
        _LOGGER.exception("Error when creating document!")
        raise RepositoryError(str(e))

    return cast(str, family_doc.import_id)


def delete(db: Session, import_id: str) -> bool:
    """
    Deletes a single document by the import id.

    :param db Session: the database connection
    :param str import_id: The document import id to delete.
    :return bool: True if deleted False if not.
    """

    found = (
        db.query(FamilyDocument)
        .filter(FamilyDocument.import_id == import_id)
        .one_or_none()
    )
    if found is None:
        return False

    # TODO: Check the backend - I think when a document is delete the
    # actual information in the physical_document is "blanked".

    result = db.execute(
        db_update(FamilyDocument)
        .where(FamilyDocument.import_id == import_id)
        .values(document_status=DocumentStatus.DELETED)
    )
    if result.rowcount == 0:  # type: ignore
        msg = f"Could not delete document : {import_id}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    return True


def count(db: Session) -> Optional[int]:
    """
    Counts the number of documents in the repository.

    :param db Session: the database connection
    :return Optional[int]: The number of documents in the repository or none.
    """
    try:
        n_documents = _get_query(db).count()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return n_documents
