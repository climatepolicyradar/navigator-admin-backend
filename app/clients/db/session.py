import logging
from typing import cast
from sqlalchemy import exc
from sqlalchemy.orm import registry, sessionmaker, Session

from app.config import SQLALCHEMY_DATABASE_URI
from app.errors import RepositoryError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


engine = create_async_engine(
    SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    # TODO: configure as part of scaling work
    pool_size=10,
    max_overflow=240,
    # echo="debug",
)
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

_LOGGER = logging.getLogger(__name__)


def make_declarative_base():
    mapper_registry = registry()
    Base = mapper_registry.generate_base()

    Base.metadata.naming_convention = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s__%(column_0_name)s",
        "ck": "ck_%(table_name)s__%(constraint_name)s",
        "fk": "fk_%(table_name)s__%(column_0_name)s__%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }

    # overwrite the SQLAlchemy __repr__ method for ORM instances
    def base_repr(self):
        values = [
            f"{col.key}={repr(getattr(self, col.key))}" for col in self.__table__.c
        ]
        return f'<Row of {self.__tablename__}: {", ".join(values)}>'

    Base.__repr__ = base_repr
    return Base


def get_db() -> AsyncSession:
    return cast(AsyncSession, SessionLocal())


Base = make_declarative_base()
# Aliased type annotation useful for type hints
AnyModel = Base


def with_transaction(module_name):
    def inner(func):
        async def wrapper(*args, **kwargs):
            db = get_db()
            try:
                db.begin()
                result = func(*args, **kwargs, db=db)
                await db.commit()
                return result
            except exc.SQLAlchemyError as e:
                msg = f"Error {str(e)} in {module_name}.{func.__name__}()"
                _LOGGER.error(
                    msg, extra={"failing_module": module_name, "func": func.__name__}
                )
                await db.rollback()
                raise RepositoryError(str(e))
            finally:
                await db.close()

        return wrapper

    return inner
