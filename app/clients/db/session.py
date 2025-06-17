import logging

from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import Session, sessionmaker

from app.config import SQLALCHEMY_DATABASE_URI, STATEMENT_TIMEOUT
from app.errors import RepositoryError

# TODO: better session handling - https://linear.app/climate-policy-radar/issue/APP-630/investigate-hypothesis-that-admin-service-backend-is-leaving-stray
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    # TODO: configure as part of scaling work: PDCT-650
    pool_size=10,
    max_overflow=240,
    # recycle after 30 minutes - this kills unused, unclosed connections
    # which we know exist because of methods calling get_db() explicity
    pool_recycle=1800,
    # wait up to 30s for a connection before error - this avoids a request hanging forever
    pool_timeout=30,
    connect_args={"options": f"-c statement_timeout={STATEMENT_TIMEOUT}"},
)
SQLAlchemyInstrumentor().instrument(engine=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

_LOGGER = logging.getLogger(__name__)


def get_db() -> Session:
    return SessionLocal()


def with_database():
    """Wraps a function and supplies the db session to it.

    This decorator is used to wrap functions that require a database session.

    NOTE: Transaction management is handled by the service functions.
    Don't be tempted to put them in here as they are unique to each service.
    """

    def inner(func):
        def wrapper(*args, **kwargs):
            context = f"{func.__module__}::{func.__name__}{args}"
            db = get_db()
            try:
                result = func(*args, **kwargs, db=db)
                return result
            except exc.SQLAlchemyError as e:
                msg = f"Error {str(e)} in {context}"
                _LOGGER.error(
                    msg,
                    extra={"failing_module": func.__module__, "func": func.__name__},
                )
                raise RepositoryError(context) from e
            finally:
                db.close()

        return wrapper

    return inner
