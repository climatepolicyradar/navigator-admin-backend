import logging
import os
from typing import Optional, Union, cast

from db_client.models.organisation import Corpus, CorpusType, Organisation
from db_client.models.organisation.counters import CountedEntity
from sqlalchemy import and_, asc, or_
from sqlalchemy import update as db_update
from sqlalchemy.exc import NoResultFound, OperationalError
from sqlalchemy.orm import Query, Session
from sqlalchemy_utils import escape_like

from app.errors import RepositoryError
from app.model.corpus import CorpusCreateDTO, CorpusReadDTO, CorpusWriteDTO
from app.repository.helpers import generate_import_id

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


def _get_query(db: Session) -> Query:
    # NOTE: SqlAlchemy will make a complete hash of query generation
    #       if columns are used in the query() call. Therefore, entire
    #       objects are returned.
    return (
        db.query(Corpus, CorpusType, Organisation)
        .join(CorpusType, Corpus.corpus_type_name == CorpusType.name)
        .join(Organisation, Corpus.organisation_id == Organisation.id)
    )


def _corpus_to_dto(
    corpus_corpus_type_org: tuple[Corpus, CorpusType, Organisation],
) -> CorpusReadDTO:
    corpus, corpus_type, org = corpus_corpus_type_org

    metadata = cast(dict, corpus_type.valid_metadata)
    return CorpusReadDTO(
        import_id=cast(str, corpus.import_id),
        title=str(corpus.title),
        description=(
            cast(str, corpus.description) if corpus.description is not None else None
        ),
        metadata=metadata,
        corpus_text=(str(corpus.corpus_text)),
        corpus_image_url=(
            cast(str, corpus.corpus_image_url)
            if corpus.corpus_image_url is not None and corpus.corpus_image_url != ""
            else None
        ),
        corpus_type_name=cast(str, corpus.corpus_type_name),
        corpus_type_description=cast(str, corpus_type.description),
        organisation_id=cast(int, org.id),
        organisation_name=cast(str, org.name),
        # TODO add created and last modified timestamps?
    )


def get_corpus_org_id(db: Session, corpus_id: str) -> Optional[int]:
    """Get the organisation ID a corpus belongs to.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to get the org
        for.
    :return Optional[int]: Return the organisation ID the given corpus
        belongs to or None.
    """
    return db.query(Corpus.organisation_id).filter_by(import_id=corpus_id).scalar()


def is_corpus_type_name_valid(db: Session, corpus_type_name: str) -> bool:
    """Check whether a corpus type name exists in the DB.

    :param Session db: The DB session to connect to.
    :param str corpus_type_name: The corpus type name we want to search
        for.
    :return bool: Whether the given corpus type exists in the db.
    """
    return bool(
        db.query(CorpusType.name).filter_by(name=corpus_type_name).scalar() is not None
    )


def verify_corpus_exists(db: Session, corpus_id: str) -> bool:
    """Validate whether a corpus with the given ID exists in the DB.

    :param Session db: The DB session to connect to.
    :param str corpus_id: The corpus import ID we want to validate.
    :return bool: Return whether or not the corpus exists in the DB.
    """
    corpora = [corpus[0] for corpus in db.query(Corpus.import_id).distinct().all()]
    return bool(corpus_id in corpora)


def all(db: Session, org_id: Optional[int]) -> list[CorpusReadDTO]:
    """
    Returns all the corpora.

    :param db Session: the database connection
    :param org_id int: the ID of the organisation the user belongs to
    :return Optional[DocumentResponse]: All of things
    """
    query = _get_query(db)
    if org_id is not None:
        query = query.filter(Organisation.id == org_id)

    result = query.order_by(asc(Corpus.title)).all()

    if not result:
        return []

    return [_corpus_to_dto(corpus) for corpus in result]


def get(db: Session, import_id: str) -> Optional[CorpusReadDTO]:
    """
    Gets a single corpus from the repository.

    :param db Session: the database connection
    :param str import_id: The import_id of the corpus
    :return Optional[CorpusReadDTO]: A single corpus or nothing
    """
    try:
        result = _get_query(db).filter(Corpus.import_id == import_id).one()
    except NoResultFound as e:
        _LOGGER.debug(e)
        return

    return _corpus_to_dto(result)


def search(
    db: Session, query_params: dict[str, Union[str, int]], org_id: Optional[int]
) -> list[CorpusReadDTO]:
    """
    Gets a list of corpora from the repository searching the title.

    :param db Session: the database connection
    :param dict query_params: Any search terms to filter on specified
        fields (title by default if 'q' specified).
    :param org_id Optional[int]: the ID of the organisation the user belongs to
    :raises HTTPException: If a DB error occurs a 503 is returned.
    :raises HTTPException: If the search request times out a 408 is
        returned.
    :return list[CorpusReadDTO]: A list of matching corpora.
    """
    search = []
    if "q" in query_params.keys():
        term = f"%{escape_like(query_params['q'])}%"
        search.append(
            or_(
                Corpus.title.ilike(term),
                Corpus.description.ilike(term),
                Corpus.corpus_text.ilike(term),
            )
        )
    else:
        if "title" in query_params.keys():
            term = f"%{escape_like(query_params['title'])}%"
            search.append(Corpus.title.ilike(term))

        if "description" in query_params.keys():
            term = f"%{escape_like(query_params['description'])}%"
            search.append(Corpus.description.ilike(term))

        if "corpus_text" in query_params.keys():
            term = f"%{escape_like(query_params['corpus_text'])}%"
            search.append(Corpus.corpus_text.ilike(term))

    condition = and_(*search) if len(search) > 1 else search[0]
    try:
        query = _get_query(db).filter(condition)
        if org_id is not None:
            query = query.filter(Organisation.id == org_id)
        result = (
            query.order_by(asc(Corpus.title)).limit(query_params["max_results"]).all()
        )
    except OperationalError as e:
        if "canceling statement due to statement timeout" in str(e):
            raise TimeoutError
        raise RepositoryError(e)

    return [_corpus_to_dto(doc) for doc in result]


def update(db: Session, import_id: str, corpus: CorpusWriteDTO) -> bool:
    """
    Updates a single entry with the new values passed.

    :param db Session: the database connection
    :param str import_id: The corpus import id to change.
    :param CorpusWriteDTO corpus: The new values
    :return bool: True if new values were set otherwise false.
    """

    new_values = corpus.model_dump()

    original_corpus, original_corpus_type, _ = (
        _get_query(db).filter(Corpus.import_id == import_id).one_or_none()
    )

    if (
        original_corpus is None or original_corpus_type is None
    ):  # Not found the corpus to update
        _LOGGER.error(f"Unable to find corpus for update {import_id}")
        return False

    # Check what has changed.
    ct_description_has_changed = (
        original_corpus_type.name != new_values["corpus_type_description"]
    )
    title_has_changed = original_corpus.title != new_values["title"]
    description_has_changed = original_corpus.description != new_values["description"]
    corpus_text_has_changed = original_corpus.corpus_text != new_values["corpus_text"]
    image_url_has_changed = original_corpus.corpus_image_url != cast(
        str, new_values["corpus_image_url"]
    )

    if not any(
        [
            ct_description_has_changed,
            title_has_changed,
            description_has_changed,
            corpus_text_has_changed,
            image_url_has_changed,
        ]
    ):
        return True

    commands = []

    # Update logic to only perform update if not idempotent.
    if ct_description_has_changed:
        commands.append(
            db_update(CorpusType)
            .where(CorpusType.name == original_corpus_type.name)
            .values(
                description=new_values["corpus_type_description"],
            )
        )

    if any(
        [
            corpus_text_has_changed,
            title_has_changed,
            description_has_changed,
            image_url_has_changed,
        ]
    ):
        commands.append(
            db_update(Corpus)
            .where(Corpus.import_id == original_corpus.import_id)
            .values(
                title=new_values["title"],
                description=new_values["description"],
                corpus_image_url=(
                    str(new_values["corpus_image_url"])
                    if new_values["corpus_image_url"] is not None
                    else None
                ),
                corpus_text=new_values["corpus_text"],
            ),
        )

    for c in commands:
        result = db.execute(c)

    if result.rowcount == 0:  # type: ignore
        msg = f"Could not update corpus fields: {corpus}"
        _LOGGER.error(msg)
        raise RepositoryError(msg)

    return True


def create(db: Session, corpus: CorpusCreateDTO) -> str:
    """Create a new corpus.

    :param db Session: the database connection
    :param CorpusCreateDTO corpus: the values for the new corpus
    :return str: The ID of the created corpus.
    """
    try:
        import_id = (
            generate_import_id(db, CountedEntity.Corpus, corpus.organisation_id)
            if corpus.import_id is None
            else corpus.import_id
        )
        new_corpus = Corpus(
            import_id=import_id,
            title=corpus.title,
            description=corpus.description,
            corpus_text=corpus.corpus_text,
            corpus_image_url=corpus.corpus_image_url,
            organisation_id=corpus.organisation_id,
            corpus_type_name=corpus.corpus_type_name,
        )
        db.add(new_corpus)
        db.flush()
    except Exception as e:
        _LOGGER.exception(f"Error trying to create Corpus: {e}")
        raise RepositoryError(e)

    return cast(str, new_corpus.import_id)
