"""Фикстуры, специфичные для модульных тестов."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from logistics.domain.enums import NodeType, TransportType
from logistics.domain.graph import TransportGraph
from logistics.domain.models import Cargo, Location, TransportLink
from logistics.domain.strategy import CheapestRouteStrategy, FastestRouteStrategy
from logistics.infrastructure.repositories import (
    ICargoRepository,
    ILocationRepository,
    IOrderRepository,
    IRouteSegmentRepository,
    ITrackingRepository,
    ITransportLinkRepository,
    IUserRepository,
)
from logistics.service.logistics_service import LogisticsService


# ── Граф (3 вершины, 3 ребра — треугольник) ──────────────────────────


@pytest.fixture()
def triangle_graph(
    sample_location_moscow,
    sample_location_spb,
    sample_location_kazan,
) -> TransportGraph:
    """Граф-треугольник: MSK→SPB, MSK→KZN, KZN→SPB.

    Ожидается, что после реализации add_node / add_edge граф будет
    содержать 3 вершины и 3 ребра.
    """
    graph = TransportGraph()

    graph.add_node(sample_location_moscow)
    graph.add_node(sample_location_spb)
    graph.add_node(sample_location_kazan)

    # Прямой MSK→SPB (ж/д, дорого + долго суммарно — для теста)
    graph.add_edge(TransportLink(
        id=1,
        source=sample_location_moscow,
        target=sample_location_spb,
        transport_type=TransportType.RAIL,
        distance_km=700,
        duration_min=480,
        cost_base=Decimal("3000.00"),
        max_weight_kg=1000.0,
        max_volume_m3=50.0,
    ))

    # MSK→KZN (авто, дёшево)
    graph.add_edge(TransportLink(
        id=2,
        source=sample_location_moscow,
        target=sample_location_kazan,
        transport_type=TransportType.ROAD,
        distance_km=800,
        duration_min=600,
        cost_base=Decimal("1000.00"),
        max_weight_kg=500.0,
        max_volume_m3=30.0,
    ))

    # KZN→SPB (авиа, быстро)
    graph.add_edge(TransportLink(
        id=3,
        source=sample_location_kazan,
        target=sample_location_spb,
        transport_type=TransportType.AIR,
        distance_km=1200,
        duration_min=120,
        cost_base=Decimal("800.00"),
        max_weight_kg=200.0,
        max_volume_m3=10.0,
    ))

    return graph


# ── Мок-репозитории ──────────────────────────────────────────────────


@pytest.fixture()
def mock_order_repo() -> IOrderRepository:
    return MagicMock(spec=IOrderRepository)


@pytest.fixture()
def mock_cargo_repo() -> ICargoRepository:
    return MagicMock(spec=ICargoRepository)


@pytest.fixture()
def mock_location_repo() -> ILocationRepository:
    return MagicMock(spec=ILocationRepository)


@pytest.fixture()
def mock_link_repo() -> ITransportLinkRepository:
    return MagicMock(spec=ITransportLinkRepository)


@pytest.fixture()
def mock_tracking_repo() -> ITrackingRepository:
    return MagicMock(spec=ITrackingRepository)


@pytest.fixture()
def mock_segment_repo() -> IRouteSegmentRepository:
    return MagicMock(spec=IRouteSegmentRepository)


@pytest.fixture()
def mock_user_repo() -> IUserRepository:
    return MagicMock(spec=IUserRepository)


@pytest.fixture()
def logistics_service(
    mock_order_repo,
    mock_cargo_repo,
    mock_location_repo,
    mock_link_repo,
    mock_tracking_repo,
    mock_segment_repo,
    mock_user_repo,
) -> LogisticsService:
    """Экземпляр LogisticsService с мок-репозиториями."""
    return LogisticsService(
        order_repo=mock_order_repo,
        cargo_repo=mock_cargo_repo,
        location_repo=mock_location_repo,
        link_repo=mock_link_repo,
        tracking_repo=mock_tracking_repo,
        segment_repo=mock_segment_repo,
        user_repo=mock_user_repo,
    )