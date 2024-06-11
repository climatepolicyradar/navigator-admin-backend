import logging
import threading

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import Session, sessionmaker

from app.config import SQLALCHEMY_DATABASE_URI, STATEMENT_TIMEOUT
from app.errors import RepositoryError

session_context = threading.local()
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    # TODO: configure as part of scaling work: PDCT-650
    pool_size=10,
    max_overflow=240,
    # echo="debug",
    connect_args={"options": f"-c statement_timeout={STATEMENT_TIMEOUT}"},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_LOGGER = logging.getLogger(__name__)


def get_db() -> Session:
    return SessionLocal()


def with_transaction(module_name, context=session_context):
    """Wraps a function with this standard transaction handler.

    Note: You still need to call commit() in the `func` if you require
    any changes to persist.

    :param _type_ module_name: The name of the module, used for logging context.
    :param _type_ context: any context object to propagate to `func`, defaults to session_context
    """

    def inner(func):
        def wrapper(*args, **kwargs):
            context.error = None
            db = get_db()
            try:
                db.begin_nested()
                result = func(*args, **kwargs, context=context, db=db)
                if db.transaction.is_active:
                    db.transaction.commit()
                return result
            except exc.SQLAlchemyError as e:
                msg = f"Error {str(e)} in {module_name}.{func.__name__}()"
                _LOGGER.error(
                    msg, extra={"failing_module": module_name, "func": func.__name__}
                )
                db.rollback()
                if context.error is not None:
                    raise RepositoryError(context.error) from e
                raise RepositoryError(str(e)) from e
            finally:
                db.close()

        return wrapper

    return inner
