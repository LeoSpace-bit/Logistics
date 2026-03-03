"""Доменные модели (чистые объекты без привязки к ORM)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from src.logistics.domain.enums import (
    NodeType,
    OrderStatus,
    TransportType,
    UserRole,
)


# ── Пользователь ─────────────────────────────────────────────────────


@dataclass
class User:
    """Пользователь системы (клиент / менеджер / администратор)."""

    login: str
    password_hash: str
    role: UserRole
    id: int | None = None
    full_name: str | None = None
    created_at: datetime | None = None


# ── Вершина графа ────────────────────────────────────────────────────


@dataclass
class Location:
    """Вершина транспортного графа (склад, аэропорт, ПВЗ и т.д.)."""

    name: str
    type: NodeType
    address: str
    id: int | None = None
    geo_lat: float | None = None
    geo_lon: float | None = None


# ── Ребро графа ──────────────────────────────────────────────────────


@dataclass
class TransportLink:
    """Ребро транспортного графа с весами и ограничениями."""

    source: Location
    target: Location
    transport_type: TransportType
    distance_km: int
    duration_min: int
    cost_base: Decimal
    id: int | None = None
    max_weight_kg: float | None = None
    max_volume_m3: float | None = None
    allows_dangerous: bool = False
    allows_fragile: bool = True
    allows_temp_control: bool = False

    def can_transport(self, cargo: Cargo) -> bool:
        """Проверить, можно ли перевезти *cargo* по этому ребру.

        Проверяет вес, объём и специальные флаги (хрупкость, опасность,
        температурный контроль).

        Returns:
            True — ограничения не нарушены, False — груз не подходит.
        """
        raise NotImplementedError


# ── Груз ─────────────────────────────────────────────────────────────


@dataclass
class Cargo:
    """Груз заказа.  Создаётся через :class:`CargoBuilder`."""

    weight_kg: float
    volume_m3: float
    id: int | None = None
    description: str = ""
    is_fragile: bool = False
    is_dangerous: bool = False
    req_temp_control: bool = False

    def validate(self) -> bool:
        """Проверить корректность параметров груза.

        Returns:
            True — параметры валидны.

        Raises:
            InvalidCargoError: вес ≤ 0, объём ≤ 0 и т.д.
        """
        raise NotImplementedError


# ── Маршрут ──────────────────────────────────────────────────────────


@dataclass
class RouteSegment:
    """Один шаг маршрута (ссылка на ребро графа + порядковый номер)."""

    link: TransportLink
    step_sequence: int
    is_completed: bool = False


@dataclass
class Route:
    """Рассчитанный маршрут (результат работы Strategy)."""

    segments: list[RouteSegment] = field(default_factory=list)
    total_cost: Decimal = Decimal("0")
    total_time_min: int = 0
    estimated_arrival: datetime | None = None


# ── Заказ ────────────────────────────────────────────────────────────


class Order:
    """Заказ на доставку — центральная сущность домена."""

    def __init__(
        self,
        sender: User,
        origin: Location,
        destination: Location,
        cargo: Cargo,
        id: uuid.UUID | None = None,
        receiver: User | None = None,
        route: Route | None = None,
        status: OrderStatus = OrderStatus.CREATED,
        total_cost: Decimal | None = None,
        estimated_delivery: datetime | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id or uuid.uuid4()
        self.sender = sender
        self.receiver = receiver
        self.origin = origin
        self.destination = destination
        self.cargo = cargo
        self.route = route
        self.status = status
        self.total_cost = total_cost
        self.estimated_delivery = estimated_delivery
        self.created_at = created_at or datetime.now()

    def update_status(self, new_status: OrderStatus) -> None:
        """Обновить статус с проверкой допустимости перехода.

        Args:
            new_status: Целевой статус.

        Raises:
            InvalidStatusTransitionError: переход не разрешён.
        """
        raise NotImplementedError

    def get_tracking_info(self) -> str:
        """Текстовое описание текущего состояния заказа."""
        raise NotImplementedError

    def assign_route(self, route: Route) -> None:
        """Привязать рассчитанный маршрут к заказу.

        Устанавливает маршрут, итоговую стоимость и прогнозное время.
        """
        raise NotImplementedError


# ── Событие отслеживания ─────────────────────────────────────────────


@dataclass
class TrackingEvent:
    """Запись журнала отслеживания (tracking_history)."""

    order_id: uuid.UUID
    status: OrderStatus
    event_time: datetime
    id: int | None = None
    location_id: int | None = None
    comment: str | None = None