"""
These tests are designed to test a real world `with_transaction()` call.

This is the decorator that is used on service calls to ensure that any
db operations are properly rolled back. However, as our tests are wrapped
in an outer transaction for speed there is some inter-play here that also
needs to be tested to ensure the testing environment is operating correctly.
"""

import pytest
from db_client.models.dfce import Family, FamilyStatus
from sqlalchemy import exc
from sqlalchemy.orm import Session, sessionmaker

from app.clients.db.session import with_database
from app.errors import RepositoryError
from app.repository.family import delete
from tests.integration_tests.setup_db import setup_db


def reconnect(bind) -> Session:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=bind)
    return SessionLocal()


def family_delete_ok(db=None):
    assert db is not None
    return delete(db, "A.0.0.3")


def family_delete_fails(db=None):
    assert db is not None
    delete(db, "A.0.0.3")
    raise exc.SQLAlchemyError("testing")


def test_with_database_when_family_delete_ok(slow_db: Session):
    saved_bind = slow_db.bind
    setup_db(slow_db)
    inner = with_database()
    wrapper = inner(family_delete_ok)
    result = wrapper()
    assert result is True
    slow_db.close()

    db = reconnect(saved_bind)
    family = db.query(Family).filter(Family.import_id == "A.0.0.3").one()
    assert family.family_status == FamilyStatus.DELETED


def test_with_database_when_family_delete_fails(slow_db: Session):
    saved_bind = slow_db.bind
    setup_db(slow_db)
    inner = with_database()
    wrapper = inner(family_delete_fails)
    with pytest.raises(RepositoryError) as e:
        wrapper()

    assert (
        e.value.message
        == "tests.integration_tests.test_with_database::family_delete_fails"
    )
    slow_db.close()

    db = reconnect(saved_bind)
    family = db.query(Family).filter(Family.import_id == "A.0.0.3").one()
    assert family.family_status == FamilyStatus.CREATED
