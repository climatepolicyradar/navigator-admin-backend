import pytest


class MockSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_get_db_yields_and_closes_session(monkeypatch):
    import app.clients.db.session as db_session

    mock_session = MockSession()
    monkeypatch.setattr(db_session, "SessionLocal", lambda: mock_session)

    assert not mock_session.closed
    with db_session.get_db_session() as db:
        assert db is mock_session
        # the session should still be open
        assert getattr(db, "closed") is False

    # Now we're outside the with-block, the session should be closed
    assert mock_session.closed is True


def test_get_db_closes_after_exception_is_thrown(monkeypatch):

    import app.clients.db.session as db_session

    mock_session = MockSession()
    monkeypatch.setattr(db_session, "SessionLocal", lambda: mock_session)

    with pytest.raises(RuntimeError):
        with db_session.get_db_session() as _:
            raise RuntimeError("broken")

    # Even though an exception was thrown, the session should be closed
    assert mock_session.closed is True
