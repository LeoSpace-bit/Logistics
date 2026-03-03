"""Фабрика приложения: инициализация БД, сервисов, сервера."""

from __future__ import annotations

from sqlalchemy.orm import Session

from logistics.infrastructure.database import create_db_engine, create_session_factory, init_db
from logistics.infrastructure.repositories import (
    SqlAlchemyCargoRepository,
    SqlAlchemyLocationRepository,
    SqlAlchemyOrderRepository,
    SqlAlchemyRouteSegmentRepository,
    SqlAlchemyTrackingRepository,
    SqlAlchemyTransportLinkRepository,
    SqlAlchemyUserRepository,
)
from logistics.infrastructure.seed import seed_database
from logistics.service.logistics_service import LogisticsService
from logistics.api.server import LogisticsServer


def create_service(session: Session) -> LogisticsService:
    """Собрать LogisticsService со всеми репозиториями."""
    return LogisticsService(
        order_repo=SqlAlchemyOrderRepository(session),
        cargo_repo=SqlAlchemyCargoRepository(session),
        location_repo=SqlAlchemyLocationRepository(session),
        link_repo=SqlAlchemyTransportLinkRepository(session),
        tracking_repo=SqlAlchemyTrackingRepository(session),
        segment_repo=SqlAlchemyRouteSegmentRepository(session),
        user_repo=SqlAlchemyUserRepository(session),
    )


def bootstrap(
    db_url: str = "sqlite:///logistics.db",
    host: str = "127.0.0.1",
    port: int = 9090,
) -> tuple[LogisticsServer, Session]:
    """Инициализировать БД, засеять, создать сервис и сервер."""
    engine = create_db_engine(db_url, echo=False)
    init_db(engine)

    session_factory = create_session_factory(engine)
    session = session_factory()

    seed_database(session)

    service = create_service(session)
    service.build_graph()

    server = LogisticsServer(host, port, service)
    return server, session