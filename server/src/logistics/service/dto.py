"""Data Transfer Objects — расширены для всех категорий груза."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class CargoCreateDTO:
    weight_kg: float
    height_m: float
    width_m: float
    length_m: float
    description: str = ""
    is_fragile: bool = False
    is_dangerous: bool = False
    is_liquid: bool = False
    is_perishable: bool = False
    is_crushable: bool = False
    req_temp_control: bool = False


@dataclass
class OrderCreateDTO:
    sender_id: int
    origin_location_id: int
    dest_location_id: int
    cargo: CargoCreateDTO
    receiver_id: int | None = None
    strategy: str = "cheapest"  # "cheapest" | "fastest"


@dataclass
class OrderResponseDTO:
    id: uuid.UUID
    status: str
    origin: str
    destination: str
    cargo_weight_kg: float
    total_cost: Decimal | None = None
    estimated_delivery: datetime | None = None
    created_at: datetime | None = None


@dataclass
class RouteSegmentDTO:
    from_location: str
    to_location: str
    transport_type: str
    duration_min: int
    cost: Decimal


@dataclass
class RouteResponseDTO:
    segments: list[RouteSegmentDTO]
    total_cost: Decimal
    total_time_min: int
    estimated_arrival: datetime | None = None


@dataclass
class TrackingEventDTO:
    status: str
    event_time: datetime
    location: str | None = None
    comment: str | None = None


@dataclass
class StatusUpdateDTO:
    order_id: uuid.UUID
    new_status: str
    comment: str | None = None
    location_id: int | None = None