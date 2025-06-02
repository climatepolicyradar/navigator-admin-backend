import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker

from app.config import SQLALCHEMY_DATABASE_URI, STATEMENT_TIMEOUT
from app.errors import RepositoryError

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


@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def with_database():
    """Wraps a function and supplies the db session to it.

    This decorator is used to wrap functions that require a database session.

    NOTE: Transaction management is handled by the service functions.
    Don't be tempted to put them in here as they are unique to each service.
    """

    def inner(func):
        def wrapper(*args, **kwargs):
            context = f"{func.__module__}::{func.__name__}{args}"
            try:
                with get_db() as db:
                    result = func(*args, **kwargs, db=db)
                    return result
            except exc.SQLAlchemyError as e:
                msg = f"Error {str(e)} in {context}"
                _LOGGER.error(
                    msg,
                    extra={"failing_module": func.__module__, "func": func.__name__},
                )
                raise RepositoryError(context) from e

        return wrapper

    return inner
