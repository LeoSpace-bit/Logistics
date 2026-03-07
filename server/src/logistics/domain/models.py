"""Доменные модели."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from logistics.domain.enums import (
    NodeType,
    OrderStatus,
    TransportType,
    UserRole,
)
from logistics.domain.exceptions import (
    InvalidCargoError,
    InvalidStatusTransitionError,
)

_VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.WAITING_DROP_OFF, OrderStatus.CANCELLED},
    OrderStatus.WAITING_DROP_OFF: {OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED},
    OrderStatus.IN_TRANSIT: {OrderStatus.ARRIVED, OrderStatus.CANCELLED},
    OrderStatus.ARRIVED: {OrderStatus.DELIVERED, OrderStatus.CANCELLED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


@dataclass
class User:
    login: str
    password_hash: str
    role: UserRole
    id: int | None = None
    full_name: str | None = None
    created_at: datetime | None = None


@dataclass
class Location:
    name: str
    type: NodeType
    address: str
    id: int | None = None
    geo_lat: float | None = None
    geo_lon: float | None = None


@dataclass
class Cargo:
    weight_kg: float
    volume_m3: float
    id: int | None = None
    description: str = ""
    is_fragile: bool = False
    is_dangerous: bool = False
    is_liquid: bool = False
    is_perishable: bool = False
    is_crushable: bool = False
    req_temp_control: bool = False

    def validate(self) -> bool:
        if self.weight_kg <= 0:
            raise InvalidCargoError(
                f"Вес груза должен быть положительным, получено: {self.weight_kg}",
            )
        if self.volume_m3 <= 0:
            raise InvalidCargoError(
                f"Объём груза должен быть положительным, получено: {self.volume_m3}",
            )
        if self.is_perishable and not self.req_temp_control:
            self.req_temp_control = True
        return True


@dataclass
class TransportLink:
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
    allows_liquid: bool = True
    allows_perishable: bool = True
    allows_crushable: bool = True
    allows_temp_control: bool = False

    def can_transport(self, cargo: Cargo) -> bool:
        if self.max_weight_kg is not None and cargo.weight_kg > self.max_weight_kg:
            return False
        if self.max_volume_m3 is not None and cargo.volume_m3 > self.max_volume_m3:
            return False
        if cargo.is_dangerous and not self.allows_dangerous:
            return False
        if cargo.is_fragile and not self.allows_fragile:
            return False
        if cargo.is_liquid and not self.allows_liquid:
            return False
        if cargo.is_perishable and not self.allows_perishable:
            return False
        if cargo.is_crushable and not self.allows_crushable:
            return False
        if cargo.req_temp_control and not self.allows_temp_control:
            return False
        return True


@dataclass
class RouteSegment:
    link: TransportLink
    step_sequence: int
    is_completed: bool = False


@dataclass
class Route:
    segments: list[RouteSegment] = field(default_factory=list)
    total_cost: Decimal = Decimal("0")
    total_time_min: int = 0
    estimated_arrival: datetime | None = None


class Order:
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

    def update_status(
        self, new_status: OrderStatus, *, force: bool = False,
    ) -> None:
        """Обновить статус. force=True пропускает проверку переходов (для ADMIN)."""
        if not force:
            allowed = _VALID_TRANSITIONS.get(self.status, set())
            if new_status not in allowed:
                raise InvalidStatusTransitionError(
                    f"Переход {self.status.value} → {new_status.value} недопустим",
                )
        self.status = new_status

    def get_tracking_info(self) -> str:
        parts = [
            f"Order {self.id}",
            f"Status: {self.status.value}",
            f"From: {self.origin.name} → To: {self.destination.name}",
            f"Cargo: {self.cargo.weight_kg} kg",
        ]
        if self.total_cost is not None:
            parts.append(f"Cost: {self.total_cost}")
        if self.estimated_delivery is not None:
            parts.append(f"ETA: {self.estimated_delivery.isoformat()}")
        return " | ".join(parts)

    def assign_route(self, route: Route) -> None:
        self.route = route
        self.total_cost = route.total_cost
        self.estimated_delivery = route.estimated_arrival


@dataclass
class TrackingEvent:
    order_id: uuid.UUID
    status: OrderStatus
    event_time: datetime
    id: int | None = None
    location_id: int | None = None
    comment: str | None = None