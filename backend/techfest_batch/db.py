from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from models.database import Base
from techfest_batch import models  # noqa: F401  (registers tables on Base)
from techfest_batch.config import settings

_engines: dict[str, Engine] = {}


def get_engine(url: str | None = None) -> Engine:
    url = url or settings.database_url
    engine = _engines.get(url)
    if engine is None:
        engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 10})
        _engines[url] = engine
    return engine


def ensure_schema(url: str | None = None) -> None:
    """Create the scenario tables if they do not exist (Alembic is the source of truth for portfolio.db)."""
    engine = get_engine(url)
    Base.metadata.create_all(
        engine,
        tables=[models.BatchJob.__table__, models.BatchCompletion.__table__],
    )


def session_factory(url: str | None = None) -> sessionmaker:
    return sessionmaker(bind=get_engine(url), autocommit=False, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(url: str | None = None) -> Iterator[Session]:
    session = session_factory(url)()
    try:
        yield session
    finally:
        session.close()


def dispose_all() -> None:
    for engine in _engines.values():
        engine.dispose()
    _engines.clear()
