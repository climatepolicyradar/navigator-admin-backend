import logging
from datetime import datetime
from typing import Optional, Tuple, Union, cast

from db_client.models.dfce import FamilyDocument
from db_client.models.dfce.family import (
    Corpus,
    DocumentStatus,
    Family,
    FamilyCorpus,
    Slug,
)
from db_client.models.document.physical_document import (
    Language,
    LanguageSource,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from db_client.models.organisation import Organisation
from db_client.models.organisation.counters import CountedEntity
from pydantic import AnyHttpUrl
from sqlalchemy import Column, and_
from sqlalchemy import delete as db_delete
from sqlalchemy import desc
from sqlalchemy import insert as db_insert
from sqlalchemy import update as db_update
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session, aliased
from sqlalchemy_utils import escape_like

from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
from app.repository import family as family_repo
from app.repository.helpers import generate_import_id, generate_slug

_LOGGER = logging.getLogger(__name__)

CreateObjects = Tuple[PhysicalDocumentLanguage, FamilyDocument, PhysicalDocument]
ReadObj = Tuple[FamilyDocument, PhysicalDocument, Organisation, Language, Language]


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of the query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.
    lang_model = aliased(Language)
    lang_user = aliased(Language)
    pdl_model = aliased(PhysicalDocumentLanguage)
    pdl_user = aliased(PhysicalDocumentLanguage)

    return (
        db.query(FamilyDocument, PhysicalDocument, Organisation, lang_user, lang_model)
        .filter(FamilyDocument.family_import_id == Family.import_id)
        .join(Family, FamilyDocument.family_import_id == Family.import_id)
        .join(
            PhysicalDocument,
            FamilyDocument.physical_document_id == PhysicalDocument.id,
            isouter=True,
        )
        .join(FamilyCorpus, FamilyCorpus.family_import_id == Family.import_id)
        .join(Corpus, Corpus.import_id == FamilyCorpus.corpus_import_id)
        .join(Organisation, Corpus.organisation_id == Organisation.id)
        .join(
            pdl_user,
            and_(
                PhysicalDocument.id == pdl_user.document_id,
                pdl_user.source == LanguageSource.USER,
            ),
            isouter=True,
        )
        .join(
            lang_user,
            lang_user.id == pdl_user.language_id,
            isouter=True,
        )
        .join(
            pdl_model,
            and_(
                PhysicalDocument.id == pdl_model.document_id,
                pdl_model.source == LanguageSource.MODEL,
            ),
            isouter=True,
        )
        .join(
            lang_model,
            lang_model.id == pdl_model.language_id,
            isouter=True,
        )
    )


def _dto_to_family_document_dict(dto: DocumentCreateDTO) -> dict:
    return {
        "family_import_id": dto.family_import_id,
        "physical_document_id": 0,
        "variant_name": dto.variant_name,
        "document_type": dto.type,
        "document_role": dto.role,
    }


def _document_tuple_from_create_dto(
    db: Session, dto: DocumentCreateDTO
) -> CreateObjects:
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
        # TODO: More verification needed here: PDCT-865
        source_url=str(dto.source_url) if dto.source_url is not None else None,
    )
    return language, fam_doc, phys_doc


def _doc_to_dto(doc_query_return: ReadObj) -> DocumentReadDTO:
    fdoc, pdoc, org, lang_user, lang_model = doc_query_return

    return DocumentReadDTO(
        import_id=str(fdoc.import_id),
        family_import_id=str(fdoc.family_import_id),
        variant_name=str(fdoc.variant_name) if fdoc.variant_name is not None else None,
        status=cast(DocumentStatus, fdoc.document_status),
        role=str(fdoc.document_role) if fdoc.document_role is not None else None,
        type=str(fdoc.document_type) if fdoc.document_type is not None else None,
        created=cast(datetime, fdoc.created),
        last_modified=cast(datetime, fdoc.last_modified),
        slug=str(fdoc.slugs[-1].name if len(fdoc.slugs) > 0 else ""),
        physical_id=cast(int, pdoc.id),
        title=str(pdoc.title),
        md5_sum=str(pdoc.md5_sum) if pdoc.md5_sum is not None else None,
        cdn_object=str(pdoc.cdn_object) if pdoc.cdn_object is not None else None,
        source_url=(
            cast(AnyHttpUrl, pdoc.source_url) if pdoc.source_url is not None else None
        ),
        content_type=str(pdoc.content_type) if pdoc.content_type is not None else None,
        user_language_name=str(lang_user.name) if lang_user is not None else None,
        calc_language_name=str(lang_model.name) if lang_model is not None else None,
    )


def all(db: Session, org_id: Optional[int]) -> list[DocumentReadDTO]:
    """
    Returns all the documents.

    :param db Session: the database connection
    :param org_id int: the ID of the organisation the user belongs to
    :return Optional[DocumentResponse]: All of things
    """
    query = _get_query(db)
    if org_id is not None:
        query = query.filter(Organisation.id == org_id)

    result = query.order_by(desc(FamilyDocument.last_modified)).all()

    if not result:
        return []

    return [_doc_to_dto(doc) for doc in result]


def get(db: Session, import_id: str) -> Optional[DocumentReadDTO]:
    """
    Gets a single document from the repository.

    :param db Session: the database connection
    :param str import_id: The import_id of the document
    :return Optional[DocumentResponse]: A single document or nothing
    """
    try:
        result = _get_query(db).filter(FamilyDocument.import_id == import_id).one()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return _doc_to_dto(result)


def search(
    db: Session, query_params: dict[str, Union[str, int]], org_id: Optional[int]
) -> list[DocumentReadDTO]:
    """
    Gets a list of documents from the repository searching the title.

    :param db Session: the database connection
    :param dict query_params: Any search terms to filter on specified
        fields (title by default if 'q' specified).
    :param org_id Optional[int]: the ID of the organisation the user belongs to
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[DocumentResponse]: A list of matching documents.
    """
    search = []
    if "q" in query_params.keys():
        term = f"%{escape_like(query_params['q'])}%"
        search.append(PhysicalDocument.title.ilike(term))

    condition = and_(*search) if len(search) > 1 else search[0]
    try:
        query = _get_query(db).filter(condition)
        if org_id is not None:
            query = query.filter(Organisation.id == org_id)
        result = (
            query.order_by(desc(FamilyDocument.last_modified))
            .limit(query_params["max_results"])
            .all()
        )
    except OperationalError as e:
        if "canceling statement due to statement timeout" in str(e):
            raise TimeoutError
        raise RepositoryError(e)

    return [_doc_to_dto(doc) for doc in result]


def update(db: Session, import_id: str, document: DocumentWriteDTO) -> bool:
    """
    Updates a single entry with the new values passed.

    :param db Session: the database connection
    :param str import_id: The document import id to change.
    :param DocumentDTO document: The new values
    :return bool: True if new values were set otherwise false.
    """

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

    # User Language changed?
    existing_language = _get_existing_language(db, original_fd)
    new_language = _get_requested_language(db, new_values)
    has_language_changed = not _is_language_equal(existing_language, new_language)

    update_slug = original_pd.title != new_values["title"]

    commands = [
        db_update(PhysicalDocument)
        .where(PhysicalDocument.id == original_pd.id)
        .values(
            title=new_values["title"],
            source_url=(
                str(new_values["source_url"])
                if new_values["source_url"] is not None
                else None
            ),
        ),
        db_update(FamilyDocument)
        .where(FamilyDocument.import_id == original_fd.import_id)
        .values(
            variant_name=new_values["variant_name"],
            document_role=new_values["role"],
            document_type=new_values["type"],
        ),
    ]

    # Update logic to only perform update if not idempotent.
    if has_language_changed:
        if new_language is not None:
            if existing_language is not None:
                command = (
                    db_update(PhysicalDocumentLanguage)
                    .where(
                        and_(
                            PhysicalDocumentLanguage.document_id
                            == original_fd.physical_document_id,
                            PhysicalDocumentLanguage.source == LanguageSource.USER,
                        )
                    )
                    .values(language_id=new_language.id)
                )
            else:
                command = db_insert(PhysicalDocumentLanguage).values(
                    document_id=original_fd.physical_document_id,
                    language_id=new_language.id,
                    source=LanguageSource.USER,
                )
            commands.append(command)

        else:
            if existing_language is not None:
                command = db_delete(PhysicalDocumentLanguage).where(
                    PhysicalDocumentLanguage.document_id
                    == original_fd.physical_document_id
                )
                commands.append(command)

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


def _get_existing_language(
    db: Session, original_fd: FamilyDocument
) -> Optional[Language]:
    existing_language = (
        db.query(PhysicalDocumentLanguage)
        .filter(
            PhysicalDocumentLanguage.document_id == original_fd.physical_document_id
        )
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one_or_none()
    )
    return existing_language


def _get_requested_language(db: Session, new_values: dict) -> Optional[Language]:
    requested_language = new_values["user_language_name"]
    if requested_language is None:
        return None

    new_language = (
        db.query(Language)
        .filter(Language.name == new_values["user_language_name"])
        .one()
    )
    return new_language


def _is_language_equal(
    existing_language: Optional[Language],
    requested_language: Optional[Language],
) -> bool:
    """Check whether the language is idempotent."""
    if (existing_language == requested_language) is None:
        return True

    if requested_language is not None:
        is_idempotent = bool(
            existing_language.language_id == requested_language.id
            if existing_language is not None
            else False
        )
        return is_idempotent

    return False


def create(db: Session, document: DocumentCreateDTO) -> str:
    """
    Creates a new document.

    :param db Session: the database connection
    :param DocumentDTO document: the values for the new document
    :param int org_id: a validated organisation id
    :return str: The import id
    """
    try:
        language, family_doc, phys_doc = _document_tuple_from_create_dto(db, document)

        db.add(phys_doc)
        db.flush()

        # Update the FamilyDocument with the new PhysicalDocument id
        family_doc.physical_document_id = phys_doc.id

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

        # Add the language link with the new PhysicalDocument id
        if language.language_id is not None:
            language.document_id = phys_doc.id
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


def count(db: Session, org_id: Optional[int]) -> Optional[int]:
    """
    Counts the number of documents in the repository.

    :param db Session: the database connection
    :param org_id Optional[int]: the ID of the organisation the user belongs to
    :return Optional[int]: The number of documents in the repository or none.
    """
    try:
        query = _get_query(db)
        if org_id is not None:
            query = query.filter(Organisation.id == org_id)
        n_documents = query.count()
    except NoResultFound:
        return

    return n_documents


def get_org_from_import_id(
    db: Session, import_id: str, is_create: bool = False
) -> Optional[int]:
    query = _get_query(db)
    if is_create:
        query = query.filter(FamilyDocument.family_import_id == import_id).distinct(
            FamilyDocument.family_import_id
        )
    else:
        query = query.filter(FamilyDocument.import_id == import_id)
    result = query.one_or_none()
    if result is None:
        return None
    _, _, org, _, _ = result
    return org.id
