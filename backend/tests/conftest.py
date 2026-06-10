import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from models.database import Base


@pytest.fixture(scope="session")
def engine():
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=eng)
    return eng


@pytest.fixture()
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    # Use SAVEPOINT so that session.commit() inside code under test
    # only commits the savepoint, preserving outer transaction for rollback.
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        if trans.nested and not trans._parent.nested:
            sess.begin_nested()

    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
