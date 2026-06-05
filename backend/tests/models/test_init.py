from models import Portfolio, Position, Transaction, History, Base, SessionLocal


class TestModelsInit:

    def test_portfolio_exported(self):
        assert Portfolio is not None

    def test_position_exported(self):
        assert Position is not None

    def test_transaction_exported(self):
        assert Transaction is not None

    def test_history_exported(self):
        assert History is not None

    def test_base_exported(self):
        assert Base is not None

    def test_session_local_exported(self):
        assert SessionLocal is not None
