import logging
from typing import Optional, Tuple, Union, cast

from sqlalchemy import Column, and_, func
from sqlalchemy import insert as db_insert
from sqlalchemy import update as db_update
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session, aliased
from sqlalchemy.sql.functions import concat
from sqlalchemy_utils import escape_like

from app.clients.db.models.app.counters import CountedEntity
from app.clients.db.models.document.physical_document import (
    Language,
    LanguageSource,
    PhysicalDocument,
    PhysicalDocumentLanguage,
)
from app.clients.db.models.law_policy import (
    FamilyDocument,
)
from app.clients.db.models.law_policy.family import (
    DocumentStatus,
    Slug,
)
from app.errors import RepositoryError, ValidationError
from app.model.document import DocumentCreateDTO, DocumentReadDTO, DocumentWriteDTO
from app.repository import family as family_repo
from app.repository.helpers import generate_import_id, generate_slug

_LOGGER = logging.getLogger(__name__)

CreateObjects = Tuple[PhysicalDocumentLanguage, FamilyDocument, PhysicalDocument]


def _get_query(db: Session) -> Query:
    lang_model = aliased(Language)
    lang_user = aliased(Language)
    pdl_model = aliased(PhysicalDocumentLanguage)
    pdl_user = aliased(PhysicalDocumentLanguage)

    sq_slug = (
        db.query(
            func.string_agg(Slug.name, ",").label("name"),
            Slug.family_document_import_id.label("doc_id"),
        )
        .group_by(Slug.family_document_import_id)
        .subquery()
    )

    return (
        db.query(
            FamilyDocument.import_id.label("import_id"),
            FamilyDocument.family_import_id.label("family_import_id"),
            FamilyDocument.variant_name.label("variant_name"),
            FamilyDocument.document_status.label("status"),
            FamilyDocument.document_role.label("role"),
            FamilyDocument.document_type.label("type"),
            concat(sq_slug.c.name).label("slug"),  # type: ignore
            PhysicalDocument.id.label("physical_id"),
            PhysicalDocument.title.label("title"),
            PhysicalDocument.md5_sum.label("md5_sum"),
            PhysicalDocument.cdn_object.label("cdn_object"),
            PhysicalDocument.source_url.label("source_url"),
            PhysicalDocument.content_type.label("content_type"),
            lang_user.name.label("user_language_name"),
            lang_model.name.label("calc_language_name"),
        )
        .select_from(FamilyDocument, PhysicalDocument)
        .filter(FamilyDocument.physical_document_id == PhysicalDocument.id)
        .join(sq_slug, sq_slug.c.doc_id == FamilyDocument.import_id, isouter=True)
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
        .distinct(FamilyDocument.import_id)
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
    result = _get_query(db).all()

    if not result:
        return []

    return [DocumentReadDTO(**dict(r)) for r in result]


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

    return DocumentReadDTO(**dict(result))


def search(
    db: Session, query_params: dict[str, Union[str, int]]
) -> list[DocumentReadDTO]:
    """
    Gets a list of documents from the repository searching the title.

    :param db Session: the database connection
    :param dict query_params: Any search terms to filter on specified
        fields (title by default if 'q' specified).
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
        result = (
            _get_query(db).filter(condition).limit(query_params["max_results"]).all()
        )
    except OperationalError as e:
        if "canceling statement due to statement timeout" in str(e):
            raise TimeoutError
        raise RepositoryError(e)

    return [DocumentReadDTO(**dict(r)) for r in result]


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
    pdl = (
        db.query(PhysicalDocumentLanguage)
        .filter(
            PhysicalDocumentLanguage.document_id == original_fd.physical_document_id
        )
        .filter(PhysicalDocumentLanguage.source == LanguageSource.USER)
        .one_or_none()
    )
    new_language = _get_new_language(db, new_values, pdl)

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

    if new_language is not None:
        if pdl is not None:
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


def _get_new_language(
    db: Session, new_values: dict, pdl: PhysicalDocumentLanguage
) -> Optional[Language]:
    requested_language = new_values["user_language_name"]
    if requested_language is None:
        return None
    else:
        new_language = (
            db.query(Language)
            .filter(Language.name == new_values["user_language_name"])
            .one()
        )
        update_language = (
            pdl.language_id != new_language.id if pdl is not None else True
        )

        if update_language:
            return new_language


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
        n_documents = db.query(FamilyDocument).count()
    except NoResultFound as e:
        _LOGGER.error(e)
        return

    return n_documents
