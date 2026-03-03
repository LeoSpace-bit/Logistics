"""Тесты LogisticsService — оркестрация бизнес-логики."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from logistics.domain.enums import OrderStatus
from logistics.domain.exceptions import (
    InvalidCargoError,
    InvalidStatusTransitionError,
    OrderNotFoundError,
    RouteNotFoundError,
)
from logistics.domain.models import (
    Cargo,
    Location,
    Order,
    Route,
    User,
)
from logistics.domain.strategy import CheapestRouteStrategy, FastestRouteStrategy
from logistics.service.dto import (
    CargoCreateDTO,
    OrderCreateDTO,
    OrderResponseDTO,
    RouteResponseDTO,
    StatusUpdateDTO,
    TrackingEventDTO,
)
from logistics.service.logistics_service import LogisticsService


# =====================================================================
#  set_strategy / build_graph
# =====================================================================


class TestSetStrategy:
    """LogisticsService.set_strategy()."""

    def test_set_cheapest(self, logistics_service: LogisticsService) -> None:
        """Установка CheapestRouteStrategy не бросает исключение."""
        logistics_service.set_strategy(CheapestRouteStrategy())

    def test_set_fastest(self, logistics_service: LogisticsService) -> None:
        """Установка FastestRouteStrategy не бросает исключение."""
        logistics_service.set_strategy(FastestRouteStrategy())


class TestBuildGraph:
    """LogisticsService.build_graph()."""

    def test_build_returns_graph(
        self,
        logistics_service: LogisticsService,
        mock_location_repo,
        mock_link_repo,
        sample_location_moscow,
        sample_location_spb,
        sample_link,
    ) -> None:
        """build_graph() загружает данные из репозиториев."""
        mock_location_repo.get_all.return_value = [
            sample_location_moscow,
            sample_location_spb,
        ]
        mock_link_repo.get_all.return_value = [sample_link]

        from logistics.domain.graph import TransportGraph

        graph = logistics_service.build_graph()
        assert isinstance(graph, TransportGraph)


# =====================================================================
#  create_order
# =====================================================================


class TestCreateOrder:
    """LogisticsService.create_order()."""

    @pytest.fixture()
    def valid_dto(self) -> OrderCreateDTO:
        return OrderCreateDTO(
            sender_id=1,
            origin_location_id=1,
            dest_location_id=2,
            cargo=CargoCreateDTO(
                weight_kg=10.0,
                height_m=0.5,
                width_m=0.4,
                length_m=0.3,
                description="Книги",
            ),
        )

    def test_create_returns_response_dto(
        self,
        logistics_service: LogisticsService,
        valid_dto: OrderCreateDTO,
        mock_user_repo,
        mock_location_repo,
        sample_user,
        sample_location_moscow,
        sample_location_spb,
    ) -> None:
        """create_order возвращает OrderResponseDTO."""
        mock_user_repo.get_by_id.return_value = sample_user
        mock_location_repo.get_by_id.side_effect = (
            lambda lid: {
                1: sample_location_moscow,
                2: sample_location_spb,
            }.get(lid)
        )

        result = logistics_service.create_order(valid_dto)
        assert isinstance(result, OrderResponseDTO)

    def test_create_order_status_created(
        self,
        logistics_service: LogisticsService,
        valid_dto: OrderCreateDTO,
        mock_user_repo,
        mock_location_repo,
        sample_user,
        sample_location_moscow,
        sample_location_spb,
    ) -> None:
        """Новый заказ получает статус CREATED."""
        mock_user_repo.get_by_id.return_value = sample_user
        mock_location_repo.get_by_id.side_effect = (
            lambda lid: {
                1: sample_location_moscow,
                2: sample_location_spb,
            }.get(lid)
        )

        result = logistics_service.create_order(valid_dto)
        assert result.status == OrderStatus.CREATED.value

    def test_create_order_has_uuid(
        self,
        logistics_service: LogisticsService,
        valid_dto: OrderCreateDTO,
        mock_user_repo,
        mock_location_repo,
        sample_user,
        sample_location_moscow,
        sample_location_spb,
    ) -> None:
        """Созданному заказу присваивается UUID."""
        mock_user_repo.get_by_id.return_value = sample_user
        mock_location_repo.get_by_id.side_effect = (
            lambda lid: {
                1: sample_location_moscow,
                2: sample_location_spb,
            }.get(lid)
        )

        result = logistics_service.create_order(valid_dto)
        assert isinstance(result.id, uuid.UUID)

    def test_create_order_invalid_cargo_raises(
        self,
        logistics_service: LogisticsService,
        mock_user_repo,
        mock_location_repo,
        sample_user,
        sample_location_moscow,
        sample_location_spb,
    ) -> None:
        """Невалидный груз (вес = 0) → InvalidCargoError."""
        mock_user_repo.get_by_id.return_value = sample_user
        mock_location_repo.get_by_id.side_effect = (
            lambda lid: {
                1: sample_location_moscow,
                2: sample_location_spb,
            }.get(lid)
        )

        bad_dto = OrderCreateDTO(
            sender_id=1,
            origin_location_id=1,
            dest_location_id=2,
            cargo=CargoCreateDTO(
                weight_kg=0.0,
                height_m=0.5,
                width_m=0.4,
                length_m=0.3,
            ),
        )
        with pytest.raises(InvalidCargoError):
            logistics_service.create_order(bad_dto)

    def test_create_order_unknown_sender_raises(
        self,
        logistics_service: LogisticsService,
        mock_user_repo,
    ) -> None:
        """Несуществующий отправитель → OrderNotFoundError."""
        mock_user_repo.get_by_id.return_value = None

        dto = OrderCreateDTO(
            sender_id=999,
            origin_location_id=1,
            dest_location_id=2,
            cargo=CargoCreateDTO(
                weight_kg=5.0, height_m=0.3, width_m=0.3, length_m=0.3,
            ),
        )
        with pytest.raises(OrderNotFoundError):
            logistics_service.create_order(dto)

    def test_create_order_unknown_location_raises(
        self,
        logistics_service: LogisticsService,
        mock_user_repo,
        mock_location_repo,
        sample_user,
    ) -> None:
        """Несуществующая локация → OrderNotFoundError."""
        mock_user_repo.get_by_id.return_value = sample_user
        mock_location_repo.get_by_id.return_value = None

        dto = OrderCreateDTO(
            sender_id=1,
            origin_location_id=999,
            dest_location_id=888,
            cargo=CargoCreateDTO(
                weight_kg=5.0, height_m=0.3, width_m=0.3, length_m=0.3,
            ),
        )
        with pytest.raises(OrderNotFoundError):
            logistics_service.create_order(dto)


# =====================================================================
#  get_order
# =====================================================================


class TestGetOrder:
    """LogisticsService.get_order()."""

    def test_get_existing_order(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
        sample_order: Order,
    ) -> None:
        """Существующий заказ → OrderResponseDTO."""
        mock_order_repo.get_by_id.return_value = sample_order
        result = logistics_service.get_order(sample_order.id)
        assert isinstance(result, OrderResponseDTO)

    def test_get_order_not_found_raises(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
    ) -> None:
        """Несуществующий заказ → OrderNotFoundError."""
        mock_order_repo.get_by_id.return_value = None
        with pytest.raises(OrderNotFoundError):
            logistics_service.get_order(uuid.uuid4())


# =====================================================================
#  list_orders_by_sender
# =====================================================================


class TestListOrdersBySender:
    """LogisticsService.list_orders_by_sender()."""

    def test_returns_list(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
        sample_order: Order,
    ) -> None:
        """Возвращается список OrderResponseDTO."""
        mock_order_repo.list_by_sender.return_value = [sample_order]
        result = logistics_service.list_orders_by_sender(1)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], OrderResponseDTO)

    def test_empty_list_for_unknown_sender(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
    ) -> None:
        """У несуществующего отправителя — пустой список."""
        mock_order_repo.list_by_sender.return_value = []
        result = logistics_service.list_orders_by_sender(999)
        assert result == []


# =====================================================================
#  update_status
# =====================================================================


class TestUpdateStatus:
    """LogisticsService.update_status()."""

    def test_valid_transition(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
        sample_order: Order,
    ) -> None:
        """Допустимый переход статуса → обновлённый DTO."""
        mock_order_repo.get_by_id.return_value = sample_order

        dto = StatusUpdateDTO(
            order_id=sample_order.id,
            new_status=OrderStatus.PROCESSING.value,
        )
        result = logistics_service.update_status(dto)
        assert isinstance(result, OrderResponseDTO)

    def test_order_not_found_raises(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
    ) -> None:
        """Несуществующий заказ → OrderNotFoundError."""
        mock_order_repo.get_by_id.return_value = None

        dto = StatusUpdateDTO(
            order_id=uuid.uuid4(),
            new_status=OrderStatus.PROCESSING.value,
        )
        with pytest.raises(OrderNotFoundError):
            logistics_service.update_status(dto)

    def test_invalid_transition_raises(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
        sample_order: Order,
    ) -> None:
        """Недопустимый переход → InvalidStatusTransitionError."""
        mock_order_repo.get_by_id.return_value = sample_order

        dto = StatusUpdateDTO(
            order_id=sample_order.id,
            new_status=OrderStatus.DELIVERED.value,
        )
        with pytest.raises(InvalidStatusTransitionError):
            logistics_service.update_status(dto)


# =====================================================================
#  get_tracking_history
# =====================================================================


class TestGetTrackingHistory:
    """LogisticsService.get_tracking_history()."""

    def test_returns_event_list(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
        mock_tracking_repo,
        sample_order: Order,
    ) -> None:
        """Возвращается список TrackingEventDTO."""
        mock_order_repo.get_by_id.return_value = sample_order
        mock_tracking_repo.get_by_order_id.return_value = []

        result = logistics_service.get_tracking_history(sample_order.id)
        assert isinstance(result, list)

    def test_order_not_found_raises(
        self,
        logistics_service: LogisticsService,
        mock_order_repo,
    ) -> None:
        """Несуществующий заказ → OrderNotFoundError."""
        mock_order_repo.get_by_id.return_value = None
        with pytest.raises(OrderNotFoundError):
            logistics_service.get_tracking_history(uuid.uuid4())


# =====================================================================
#  calculate_route
# =====================================================================


class TestCalculateRoute:
    """LogisticsService.calculate_route()."""

    def test_returns_route_response(
        self,
        logistics_service: LogisticsService,
        mock_location_repo,
        mock_link_repo,
        sample_location_moscow,
        sample_location_spb,
        sample_link,
    ) -> None:
        """calculate_route возвращает RouteResponseDTO."""
        mock_location_repo.get_by_id.side_effect = (
            lambda lid: {
                1: sample_location_moscow,
                2: sample_location_spb,
            }.get(lid)
        )
        mock_location_repo.get_all.return_value = [
            sample_location_moscow,
            sample_location_spb,
        ]
        mock_link_repo.get_all.return_value = [sample_link]

        logistics_service.set_strategy(CheapestRouteStrategy())
        result = logistics_service.calculate_route(
            origin_id=1,
            dest_id=2,
            weight_kg=5.0,
            volume_m3=0.05,
        )
        assert isinstance(result, RouteResponseDTO)

    def test_route_cost_positive(
        self,
        logistics_service: LogisticsService,
        mock_location_repo,
        mock_link_repo,
        sample_location_moscow,
        sample_location_spb,
        sample_link,
    ) -> None:
        """Стоимость рассчитанного маршрута > 0."""
        mock_location_repo.get_by_id.side_effect = (
            lambda lid: {
                1: sample_location_moscow,
                2: sample_location_spb,
            }.get(lid)
        )
        mock_location_repo.get_all.return_value = [
            sample_location_moscow,
            sample_location_spb,
        ]
        mock_link_repo.get_all.return_value = [sample_link]

        logistics_service.set_strategy(CheapestRouteStrategy())
        result = logistics_service.calculate_route(
            origin_id=1,
            dest_id=2,
            weight_kg=5.0,
            volume_m3=0.05,
        )
        assert result.total_cost > 0

    def test_unknown_origin_raises(
        self,
        logistics_service: LogisticsService,
        mock_location_repo,
    ) -> None:
        """Несуществующая точка отправления → RouteNotFoundError."""
        mock_location_repo.get_by_id.return_value = None

        logistics_service.set_strategy(CheapestRouteStrategy())
        with pytest.raises((RouteNotFoundError, OrderNotFoundError)):
            logistics_service.calculate_route(
                origin_id=999,
                dest_id=2,
                weight_kg=5.0,
                volume_m3=0.05,
            )

    def test_no_strategy_raises(
        self,
        logistics_service: LogisticsService,
    ) -> None:
        """Стратегия не установлена → ошибка."""
        with pytest.raises(Exception):
            logistics_service.calculate_route(
                origin_id=1,
                dest_id=2,
                weight_kg=5.0,
                volume_m3=0.05,
            )