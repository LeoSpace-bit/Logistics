"""Тесты модели Order — управление статусами и маршрутом."""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest

from logistics.domain.enums import NodeType, OrderStatus, TransportType
from logistics.domain.exceptions import InvalidStatusTransitionError
from logistics.domain.models import (
    Cargo,
    Location,
    Order,
    Route,
    RouteSegment,
    TransportLink,
)


class TestOrderUpdateStatus:
    """Order.update_status() — переходы статуса."""

    def test_created_to_processing(self, sample_order: Order) -> None:
        """CREATED → PROCESSING — допустимый переход."""
        sample_order.update_status(OrderStatus.PROCESSING)
        assert sample_order.status == OrderStatus.PROCESSING

    def test_processing_to_in_transit(self, sample_order: Order) -> None:
        """PROCESSING → WAITING_DROP_OFF — допустимый переход."""
        sample_order.update_status(OrderStatus.PROCESSING)
        sample_order.update_status(OrderStatus.WAITING_DROP_OFF)
        assert sample_order.status == OrderStatus.WAITING_DROP_OFF

    def test_in_transit_to_arrived(self, sample_order: Order) -> None:
        """IN_TRANSIT → ARRIVED — допустимый переход."""
        sample_order.update_status(OrderStatus.PROCESSING)
        sample_order.update_status(OrderStatus.WAITING_DROP_OFF)
        sample_order.update_status(OrderStatus.IN_TRANSIT)
        sample_order.update_status(OrderStatus.ARRIVED)
        assert sample_order.status == OrderStatus.ARRIVED

    def test_arrived_to_delivered(self, sample_order: Order) -> None:
        """ARRIVED → DELIVERED — финальный переход."""
        sample_order.update_status(OrderStatus.PROCESSING)
        sample_order.update_status(OrderStatus.WAITING_DROP_OFF)
        sample_order.update_status(OrderStatus.IN_TRANSIT)
        sample_order.update_status(OrderStatus.ARRIVED)
        sample_order.update_status(OrderStatus.DELIVERED)
        assert sample_order.status == OrderStatus.DELIVERED

    def test_created_to_cancelled(self, sample_order: Order) -> None:
        """CREATED → CANCELLED — допустимая отмена."""
        sample_order.update_status(OrderStatus.CANCELLED)
        assert sample_order.status == OrderStatus.CANCELLED

    def test_delivered_to_created_raises(self, sample_order: Order) -> None:
        """DELIVERED → CREATED — недопустимый откат."""
        # Сначала доводим до DELIVERED
        sample_order.update_status(OrderStatus.PROCESSING)
        sample_order.update_status(OrderStatus.WAITING_DROP_OFF)
        sample_order.update_status(OrderStatus.IN_TRANSIT)
        sample_order.update_status(OrderStatus.ARRIVED)
        sample_order.update_status(OrderStatus.DELIVERED)
        with pytest.raises(InvalidStatusTransitionError):
            sample_order.update_status(OrderStatus.CREATED)

    def test_cancelled_to_in_transit_raises(
        self, sample_order: Order,
    ) -> None:
        """CANCELLED → IN_TRANSIT — из отменённого нельзя возобновить."""
        sample_order.update_status(OrderStatus.CANCELLED)
        with pytest.raises(InvalidStatusTransitionError):
            sample_order.update_status(OrderStatus.IN_TRANSIT)

    def test_same_status_raises(self, sample_order: Order) -> None:
        """CREATED → CREATED — тот же статус, ошибка."""
        with pytest.raises(InvalidStatusTransitionError):
            sample_order.update_status(OrderStatus.CREATED)

    def test_skip_status_raises(self, sample_order: Order) -> None:
        """CREATED → IN_TRANSIT — пропуск промежуточных этапов."""
        with pytest.raises(InvalidStatusTransitionError):
            sample_order.update_status(OrderStatus.IN_TRANSIT)


class TestOrderGetTrackingInfo:
    """Order.get_tracking_info() — текстовое описание."""

    def test_returns_string(self, sample_order: Order) -> None:
        """Метод возвращает строку."""
        info = sample_order.get_tracking_info()
        assert isinstance(info, str)

    def test_contains_status(self, sample_order: Order) -> None:
        """Строка содержит текущий статус."""
        info = sample_order.get_tracking_info()
        assert "CREATED" in info

    def test_contains_order_id(self, sample_order: Order) -> None:
        """Строка содержит ID заказа."""
        info = sample_order.get_tracking_info()
        assert str(sample_order.id) in info


class TestOrderAssignRoute:
    """Order.assign_route() — привязка маршрута."""

    def test_assign_sets_route(
        self,
        sample_order: Order,
        sample_link: TransportLink,
    ) -> None:
        """После assign_route маршрут доступен через order.route."""
        segment = RouteSegment(link=sample_link, step_sequence=1)
        route = Route(
            segments=[segment],
            total_cost=Decimal("1500.00"),
            total_time_min=480,
        )
        sample_order.assign_route(route)
        assert sample_order.route is not None
        assert len(sample_order.route.segments) == 1

    def test_assign_sets_total_cost(
        self,
        sample_order: Order,
        sample_link: TransportLink,
    ) -> None:
        """После assign_route стоимость заказа обновляется."""
        route = Route(
            segments=[RouteSegment(link=sample_link, step_sequence=1)],
            total_cost=Decimal("1500.00"),
            total_time_min=480,
        )
        sample_order.assign_route(route)
        assert sample_order.total_cost == Decimal("1500.00")

    def test_assign_sets_estimated_delivery(
        self,
        sample_order: Order,
        sample_link: TransportLink,
    ) -> None:
        """После assign_route прогнозная дата доставки устанавливается."""
        arrival = datetime(2025, 7, 20, 12, 0)
        route = Route(
            segments=[RouteSegment(link=sample_link, step_sequence=1)],
            total_cost=Decimal("1500.00"),
            total_time_min=480,
            estimated_arrival=arrival,
        )
        sample_order.assign_route(route)
        assert sample_order.estimated_delivery == arrival


class TestOrderInit:
    """Проверка начальных значений при создании Order."""

    def test_default_status_is_created(self, sample_order: Order) -> None:
        """Статус по умолчанию — CREATED."""
        assert sample_order.status == OrderStatus.CREATED

    def test_id_is_uuid(self, sample_order: Order) -> None:
        """ID — объект UUID."""
        assert isinstance(sample_order.id, uuid.UUID)

    def test_created_at_is_set(self, sample_order: Order) -> None:
        """created_at заполняется автоматически."""
        assert isinstance(sample_order.created_at, datetime)

    def test_route_initially_none(self, sample_order: Order) -> None:
        """Маршрут при создании отсутствует."""
        assert sample_order.route is None