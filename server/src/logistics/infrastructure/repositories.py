"""Репозитории: абстрактные интерфейсы + SQLAlchemy-реализации."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.logistics.domain.enums import OrderStatus
from src.logistics.domain.models import (
    Cargo,
    Location,
    Order,
    RouteSegment,
    TrackingEvent,
    TransportLink,
    User,
)


# =====================================================================
#  Абстрактные интерфейсы (контракты)
# =====================================================================


class IUserRepository(ABC):
    """Интерфейс репозитория пользователей."""

    @abstractmethod
    def get_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def get_by_login(self, login: str) -> User | None: ...

    @abstractmethod
    def save(self, user: User) -> User: ...


class ILocationRepository(ABC):
    """Интерфейс репозитория локаций (вершин графа)."""

    @abstractmethod
    def get_by_id(self, location_id: int) -> Location | None: ...

    @abstractmethod
    def get_all(self) -> list[Location]: ...


class ITransportLinkRepository(ABC):
    """Интерфейс репозитория транспортных соединений (рёбер графа)."""

    @abstractmethod
    def get_all(self) -> list[TransportLink]: ...

    @abstractmethod
    def get_by_origin(self, location_id: int) -> list[TransportLink]: ...


class IOrderRepository(ABC):
    """Интерфейс репозитория заказов."""

    @abstractmethod
    def get_by_id(self, order_id: uuid.UUID) -> Order | None: ...

    @abstractmethod
    def save(self, order: Order) -> Order: ...

    @abstractmethod
    def update_status(
        self, order_id: uuid.UUID, status: OrderStatus,
    ) -> bool: ...

    @abstractmethod
    def list_by_sender(self, sender_id: int) -> list[Order]: ...


class ICargoRepository(ABC):
    """Интерфейс репозитория грузов."""

    @abstractmethod
    def save(self, cargo: Cargo, order_id: uuid.UUID) -> Cargo: ...

    @abstractmethod
    def get_by_order_id(self, order_id: uuid.UUID) -> Cargo | None: ...


class ITrackingRepository(ABC):
    """Интерфейс репозитория событий отслеживания."""

    @abstractmethod
    def add_event(self, event: TrackingEvent) -> TrackingEvent: ...

    @abstractmethod
    def get_by_order_id(
        self, order_id: uuid.UUID,
    ) -> list[TrackingEvent]: ...


class IRouteSegmentRepository(ABC):
    """Интерфейс репозитория сегментов маршрута."""

    @abstractmethod
    def save_segments(
        self, order_id: uuid.UUID, segments: list[RouteSegment],
    ) -> None: ...

    @abstractmethod
    def get_by_order_id(
        self, order_id: uuid.UUID,
    ) -> list[RouteSegment]: ...


# =====================================================================
#  SQLAlchemy-реализации
# =====================================================================


class SqlAlchemyUserRepository(IUserRepository):
    """Реализация IUserRepository поверх SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    def get_by_login(self, login: str) -> User | None:
        raise NotImplementedError

    def save(self, user: User) -> User:
        raise NotImplementedError


class SqlAlchemyLocationRepository(ILocationRepository):
    """Реализация ILocationRepository поверх SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, location_id: int) -> Location | None:
        raise NotImplementedError

    def get_all(self) -> list[Location]:
        raise NotImplementedError


class SqlAlchemyTransportLinkRepository(ITransportLinkRepository):
    """Реализация ITransportLinkRepository поверх SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[TransportLink]:
        raise NotImplementedError

    def get_by_origin(self, location_id: int) -> list[TransportLink]:
        raise NotImplementedError


class SqlAlchemyOrderRepository(IOrderRepository):
    """Реализация IOrderRepository поверх SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        raise NotImplementedError

    def save(self, order: Order) -> Order:
        raise NotImplementedError

    def update_status(
        self, order_id: uuid.UUID, status: OrderStatus,
    ) -> bool:
        raise NotImplementedError

    def list_by_sender(self, sender_id: int) -> list[Order]:
        raise NotImplementedError


class SqlAlchemyCargoRepository(ICargoRepository):
    """Реализация ICargoRepository поверх SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, cargo: Cargo, order_id: uuid.UUID) -> Cargo:
        raise NotImplementedError

    def get_by_order_id(self, order_id: uuid.UUID) -> Cargo | None:
        raise NotImplementedError


class SqlAlchemyTrackingRepository(ITrackingRepository):
    """Реализация ITrackingRepository поверх SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_event(self, event: TrackingEvent) -> TrackingEvent:
        raise NotImplementedError

    def get_by_order_id(
        self, order_id: uuid.UUID,
    ) -> list[TrackingEvent]:
        raise NotImplementedError


class SqlAlchemyRouteSegmentRepository(IRouteSegmentRepository):
    """Реализация IRouteSegmentRepository поверх SQLAlchemy."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def save_segments(
        self, order_id: uuid.UUID, segments: list[RouteSegment],
    ) -> None:
        raise NotImplementedError

    def get_by_order_id(
        self, order_id: uuid.UUID,
    ) -> list[RouteSegment]:
        raise NotImplementedError