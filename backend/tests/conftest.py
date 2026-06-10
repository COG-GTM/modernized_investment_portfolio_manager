import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
