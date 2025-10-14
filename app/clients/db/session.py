"""
Code for DB session management.

Notes from nav-backend: August 27th 2025.

We have been trying to trace segfault issues for months. They're
our white whale. We identified a hypothesis: the sqlalchemy engine
and session were initialised on module import, before uvicorn
spawned the worker processes. This meant that the engine and session
were shared across all workers. Ruh roh. SQLALCHEMY ISNT THREAD SAFE.

Update: October 2025.
Hypothesis is that stray connection leaks are being caused by services calling get_db()
without closing sessions via the defensive programming pattern below where cleanup
wasn't implemented properly.

if db is None:
    db = db_session.get_db()
...

rather than

if db is None:
    with db_session.get_db() as session:
        ...
"""

import logging
from contextlib import contextmanager
from typing import Generator

from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import Session, sessionmaker

from app.config import SQLALCHEMY_DATABASE_URI, STATEMENT_TIMEOUT
from app.errors import RepositoryError

_LOGGER = logging.getLogger(__name__)

# Engine with connection pooling to prevent connection leaks
engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,  # Verify connections before use
    pool_size=10,  # Base connection pool size
    max_overflow=20,  # Additional connections when pool exhausted - TODO: TOO HIGH?
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_timeout=30,  # Wait up to 30s for a connection before error
    connect_args={"options": f"-c statement_timeout={STATEMENT_TIMEOUT}"},
)

# OpenTelemetry instrumentation
SQLAlchemyInstrumentor().instrument(engine=engine)


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in service layer.

    Ensures sessions are properly closed via context management.

    Usage:
        with get_db() as db:
            # Use db here
            ...

    :return: Database session generator
    :rtype: Generator[Session, None, None]
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def with_database():
    """
    Decorator that wraps a function and supplies a db session to it.

    The session is automatically closed after the function executes.

    NOTE: Transaction management is handled by the service functions.
    Don't be tempted to put them in here as they are unique to each
    service.

    :return: Decorated function with database session
    :rtype: Callable
    """

    def inner(func):
        def wrapper(*args, **kwargs):
            context = f"{func.__module__}::{func.__name__}{args}"
            with get_db() as db:
                try:
                    result = func(*args, **kwargs, db=db)
                    return result
                except exc.SQLAlchemyError as e:
                    msg = f"Error {str(e)} in {context}"
                    _LOGGER.error(
                        msg,
                        extra={
                            "failing_module": func.__module__,
                            "func": func.__name__,
                        },
                    )
                    raise RepositoryError(context) from e

        return wrapper

    return inner
