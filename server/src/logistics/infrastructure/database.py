"""Настройка SQLAlchemy: engine, фабрика сессий, инициализация БД."""

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session


DATABASE_URL: str = "sqlite:///logistics.db"


def create_db_engine(url: str = DATABASE_URL, echo: bool = False) -> Engine:
    """Создать движок SQLAlchemy.

    Args:
        url: Строка подключения к БД.
        echo: Включить SQL-логирование.
    """
    return create_engine(url, echo=echo)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Создать фабрику сессий, привязанную к движку."""
    return sessionmaker(bind=engine)


def init_db(engine: Engine) -> None:
    """Создать все таблицы (DDL) по метаданным ORM."""
    from logistics.infrastructure.orm import Base
    Base.metadata.create_all(engine)