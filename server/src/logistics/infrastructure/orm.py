"""SQLAlchemy ORM — расширенные модели с новыми категориями груза."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="CLIENT")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    sent_orders: Mapped[list[OrderORM]] = relationship(
        back_populates="sender", foreign_keys="OrderORM.sender_id",
    )


class LocationORM(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    geo_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    geo_lon: Mapped[float | None] = mapped_column(Float, nullable=True)


class TransportLinkORM(Base):
    __tablename__ = "transport_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    from_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    to_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    transport_type: Mapped[str] = mapped_column(String(50), nullable=False)
    distance_km: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    cost_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    max_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_volume_m3: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Ограничения по категориям груза ───────────────────────────────
    allows_dangerous: Mapped[bool] = mapped_column(Boolean, default=False)
    allows_fragile: Mapped[bool] = mapped_column(Boolean, default=True)
    allows_liquid: Mapped[bool] = mapped_column(Boolean, default=True)
    allows_perishable: Mapped[bool] = mapped_column(Boolean, default=True)
    allows_crushable: Mapped[bool] = mapped_column(Boolean, default=True)
    allows_temp_control: Mapped[bool] = mapped_column(Boolean, default=False)

    from_location: Mapped[LocationORM] = relationship(foreign_keys=[from_location_id])
    to_location: Mapped[LocationORM] = relationship(foreign_keys=[to_location_id])


class OrderORM(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    origin_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    dest_location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), nullable=False)
    current_status: Mapped[str] = mapped_column(String(50), default="CREATED")
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_delivery: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    sender: Mapped[UserORM] = relationship(back_populates="sent_orders", foreign_keys=[sender_id])
    receiver: Mapped[UserORM | None] = relationship(foreign_keys=[receiver_id])
    origin: Mapped[LocationORM] = relationship(foreign_keys=[origin_location_id])
    destination: Mapped[LocationORM] = relationship(foreign_keys=[dest_location_id])
    cargo: Mapped[CargoORM | None] = relationship(back_populates="order", uselist=False)
    route_segments: Mapped[list[OrderRouteSegmentORM]] = relationship(back_populates="order")
    tracking_history: Mapped[list[TrackingHistoryORM]] = relationship(back_populates="order")


class CargoORM(Base):
    __tablename__ = "cargo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), unique=True, nullable=False)

    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    volume_m3: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Категории груза ───────────────────────────────────────────────
    is_fragile: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dangerous: Mapped[bool] = mapped_column(Boolean, default=False)
    is_liquid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_perishable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_crushable: Mapped[bool] = mapped_column(Boolean, default=False)
    req_temp_control: Mapped[bool] = mapped_column(Boolean, default=False)

    order: Mapped[OrderORM] = relationship(back_populates="cargo")


class OrderRouteSegmentORM(Base):
    __tablename__ = "order_route_segments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    link_id: Mapped[int] = mapped_column(ForeignKey("transport_links.id"), nullable=False)
    step_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    order: Mapped[OrderORM] = relationship(back_populates="route_segments")
    link: Mapped[TransportLinkORM] = relationship()


class TrackingHistoryORM(Base):
    __tablename__ = "tracking_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    status_code: Mapped[str] = mapped_column(String(50), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped[OrderORM] = relationship(back_populates="tracking_history")
    location: Mapped[LocationORM | None] = relationship()