import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import sessionmaker

from models.database import Base, Portfolio, Position
from models.transactions import Transaction
from models.history import History


class TestDatabaseSetup:

    def test_base_exists(self):
        assert isinstance(Base, DeclarativeMeta)

    def test_engine_creation(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        assert engine is not None
        engine.dispose()

    def test_session_creation(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = Session()
        assert session is not None
        session.close()
        engine.dispose()

    def test_create_all_tables(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        engine.dispose()

    def test_tables_exist(self):
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "portfolios" in table_names
        assert "positions" in table_names
        assert "transactions" in table_names
        assert "history" in table_names
        engine.dispose()


class TestDatabaseModels:

    def test_portfolio_table_name(self):
        assert Portfolio.__tablename__ == "portfolios"

    def test_position_table_name(self):
        assert Position.__tablename__ == "positions"

    def test_transaction_table_name(self):
        assert Transaction.__tablename__ == "transactions"

    def test_history_table_name(self):
        assert History.__tablename__ == "history"
