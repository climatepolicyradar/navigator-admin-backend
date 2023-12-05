import logging

from sqlalchemy import create_engine, exc
from sqlalchemy.orm import Session, registry, sessionmaker

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


def get_db() -> Session:
    return SessionLocal()


Base = make_declarative_base()
# Aliased type annotation useful for type hints
AnyModel = Base


def with_transaction(module_name):
    def inner(func):
        def wrapper(*args, **kwargs):
            db = get_db()
            try:
                db.begin()
                result = func(*args, **kwargs, db=db)
                db.commit()
                return result
            except exc.SQLAlchemyError as e:
                msg = f"Error {str(e)} in {module_name}.{func.__name__}()"
                _LOGGER.error(
                    msg, extra={"failing_module": module_name, "func": func.__name__}
                )
                db.rollback()
                raise RepositoryError(str(e))
            finally:
                db.close()

        return wrapper

    return inner
