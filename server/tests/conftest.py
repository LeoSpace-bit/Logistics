"""Общие фикстуры для всех тестов."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from logistics.domain.enums import (
    NodeType,
    OrderStatus,
    TransportType,
    UserRole,
)
from logistics.domain.models import (
    Cargo,
    Location,
    Order,
    Route,
    RouteSegment,
    TransportLink,
    User,
)
from logistics.infrastructure.orm import Base


# ── БД ────────────────────────────────────────────────────────────────


@pytest.fixture()
def engine():
    """In-memory SQLite движок."""
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def db_session(engine) -> Session:
    """Сессия, откатываемая после каждого теста."""
    factory = sessionmaker(bind=engine)
    session = factory()
    yield session
    session.rollback()
    session.close()


# ── Доменные объекты-заготовки ────────────────────────────────────────


@pytest.fixture()
def sample_user() -> User:
    """Тестовый пользователь (клиент)."""
    return User(
        id=1,
        login="test_client",
        password_hash="hashed_pw",
        role=UserRole.CLIENT,
        full_name="Иван Иванов",
        created_at=datetime(2025, 1, 1),
    )


@pytest.fixture()
def sample_location_moscow() -> Location:
    """Локация «Москва-Склад»."""
    return Location(
        id=1,
        name="Москва-Склад",
        type=NodeType.WAREHOUSE,
        address="г. Москва, ул. Складская, 1",
        geo_lat=55.7558,
        geo_lon=37.6173,
    )


@pytest.fixture()
def sample_location_spb() -> Location:
    """Локация «СПб-ПВЗ»."""
    return Location(
        id=2,
        name="СПб-ПВЗ",
        type=NodeType.PICKUP_POINT,
        address="г. Санкт-Петербург, Невский пр., 10",
        geo_lat=59.9343,
        geo_lon=30.3351,
    )


@pytest.fixture()
def sample_location_kazan() -> Location:
    """Локация «Казань-Хаб»."""
    return Location(
        id=3,
        name="Казань-Хаб",
        type=NodeType.HUB,
        address="г. Казань, ул. Логистическая, 5",
        geo_lat=55.7961,
        geo_lon=49.1064,
    )


@pytest.fixture()
def sample_cargo() -> Cargo:
    """Тестовый груз."""
    return Cargo(
        weight_kg=10.0,
        volume_m3=0.05,
        description="Книги",
        is_fragile=False,
        is_dangerous=False,
    )


@pytest.fixture()
def fragile_cargo() -> Cargo:
    """Хрупкий груз."""
    return Cargo(
        weight_kg=2.0,
        volume_m3=0.02,
        description="Хрустальная ваза",
        is_fragile=True,
        is_dangerous=False,
    )


@pytest.fixture()
def dangerous_cargo() -> Cargo:
    """Опасный груз."""
    return Cargo(
        weight_kg=25.0,
        volume_m3=0.1,
        description="Химреактивы",
        is_fragile=False,
        is_dangerous=True,
    )


@pytest.fixture()
def sample_link(
    sample_location_moscow,
    sample_location_spb,
) -> TransportLink:
    """Ребро «Москва → СПб» (ж/д)."""
    return TransportLink(
        id=1,
        source=sample_location_moscow,
        target=sample_location_spb,
        transport_type=TransportType.RAIL,
        distance_km=700,
        duration_min=480,
        cost_base=Decimal("1500.00"),
        max_weight_kg=1000.0,
        max_volume_m3=50.0,
        allows_dangerous=False,
        allows_fragile=True,
    )


@pytest.fixture()
def air_link(
    sample_location_moscow,
    sample_location_spb,
) -> TransportLink:
    """Ребро «Москва → СПб» (авиа — дорого, быстро)."""
    return TransportLink(
        id=2,
        source=sample_location_moscow,
        target=sample_location_spb,
        transport_type=TransportType.AIR,
        distance_km=650,
        duration_min=90,
        cost_base=Decimal("5000.00"),
        max_weight_kg=500.0,
        max_volume_m3=20.0,
        allows_dangerous=True,
        allows_fragile=True,
    )


@pytest.fixture()
def sample_order(
    sample_user,
    sample_location_moscow,
    sample_location_spb,
    sample_cargo,
) -> Order:
    """Тестовый заказ в статусе CREATED."""
    return Order(
        sender=sample_user,
        origin=sample_location_moscow,
        destination=sample_location_spb,
        cargo=sample_cargo,
        status=OrderStatus.CREATED,
    )