"""Общие фикстуры для всех тестов."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.logistics.infrastructure.orm import Base


@pytest.fixture()
def engine():
    """In-memory SQLite движок."""
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Session:              # type: ignore[type-arg]
    """Сессия, откатываемая после каждого теста."""
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.rollback()
    session.close()