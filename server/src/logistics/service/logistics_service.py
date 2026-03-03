"""Главный сервис приложения — расширен для всех категорий груза."""

from __future__ import annotations

import uuid
from datetime import datetime

from logistics.domain.builder import CargoBuilder
from logistics.domain.enums import OrderStatus, TransportType
from logistics.domain.exceptions import (
    InvalidStatusTransitionError,
    OrderNotFoundError,
    RouteNotFoundError,
)
from logistics.domain.graph import TransportGraph
from logistics.domain.models import Cargo, Order, TrackingEvent
from logistics.domain.strategy import (
    CheapestRouteStrategy,
    FastestRouteStrategy,
    IRouteStrategy,
)
from logistics.infrastructure.repositories import (
    ICargoRepository,
    ILocationRepository,
    IOrderRepository,
    IRouteSegmentRepository,
    ITrackingRepository,
    ITransportLinkRepository,
    IUserRepository,
)
from logistics.service.dto import (
    OrderCreateDTO,
    OrderResponseDTO,
    RouteResponseDTO,
    RouteSegmentDTO,
    StatusUpdateDTO,
    TrackingEventDTO,
)

_STRATEGIES: dict[str, type[IRouteStrategy]] = {
    "cheapest": CheapestRouteStrategy,
    "fastest": FastestRouteStrategy,
}


class LogisticsService:

    def __init__(
        self,
        order_repo: IOrderRepository,
        cargo_repo: ICargoRepository,
        location_repo: ILocationRepository,
        link_repo: ITransportLinkRepository,
        tracking_repo: ITrackingRepository,
        segment_repo: IRouteSegmentRepository,
        user_repo: IUserRepository,
    ) -> None:
        self._order_repo = order_repo
        self._cargo_repo = cargo_repo
        self._location_repo = location_repo
        self._link_repo = link_repo
        self._tracking_repo = tracking_repo
        self._segment_repo = segment_repo
        self._user_repo = user_repo
        self._strategy: IRouteStrategy | None = None
        self._graph: TransportGraph | None = None

    @staticmethod
    def _order_to_dto(order: Order) -> OrderResponseDTO:
        status = order.status.value if isinstance(order.status, OrderStatus) else order.status
        return OrderResponseDTO(
            id=order.id, status=status,
            origin=order.origin.name, destination=order.destination.name,
            cargo_weight_kg=order.cargo.weight_kg,
            total_cost=order.total_cost,
            estimated_delivery=order.estimated_delivery,
            created_at=order.created_at,
        )

    # ── Стратегия и граф ──────────────────────────────────────────────

    def set_strategy(self, strategy: IRouteStrategy) -> None:
        self._strategy = strategy

    def build_graph(self) -> TransportGraph:
        graph = TransportGraph()
        for loc in self._location_repo.get_all():
            graph.add_node(loc)
        for link in self._link_repo.get_all():
            graph.add_edge(link)
        self._graph = graph
        return graph

    # ── Создание заказа ───────────────────────────────────────────────

    def create_order(self, dto: OrderCreateDTO) -> OrderResponseDTO:
        sender = self._user_repo.get_by_id(dto.sender_id)
        if sender is None:
            raise OrderNotFoundError(f"Отправитель id={dto.sender_id} не найден")

        origin = self._location_repo.get_by_id(dto.origin_location_id)
        if origin is None:
            raise OrderNotFoundError(f"Локация отправления id={dto.origin_location_id} не найдена")
        destination = self._location_repo.get_by_id(dto.dest_location_id)
        if destination is None:
            raise OrderNotFoundError(f"Локация назначения id={dto.dest_location_id} не найдена")

        builder = CargoBuilder()
        builder.set_weight(dto.cargo.weight_kg)
        builder.set_dimensions(dto.cargo.height_m, dto.cargo.width_m, dto.cargo.length_m)
        builder.set_description(dto.cargo.description)
        if dto.cargo.is_fragile:
            builder.mark_as_fragile()
        if dto.cargo.is_dangerous:
            builder.mark_as_dangerous()
        if dto.cargo.is_liquid:
            builder.mark_as_liquid()
        if dto.cargo.is_perishable:
            builder.mark_as_perishable()
        if dto.cargo.is_crushable:
            builder.mark_as_crushable()
        if dto.cargo.req_temp_control:
            builder.require_temp_control()
        cargo = builder.build()  # может бросить InvalidCargoError

        receiver = None
        if dto.receiver_id is not None:
            receiver = self._user_repo.get_by_id(dto.receiver_id)

        order = Order(sender=sender, origin=origin, destination=destination, cargo=cargo, receiver=receiver)

        # Стратегия из DTO или текущая
        strategy = self._strategy
        if dto.strategy and dto.strategy in _STRATEGIES:
            strategy = _STRATEGIES[dto.strategy]()

        if strategy is not None:
            if self._graph is None:
                self.build_graph()
            try:
                route = strategy.calculate_route(self._graph, origin, destination, cargo)
                order.assign_route(route)
            except RouteNotFoundError:
                pass

        self._order_repo.save(order)
        self._cargo_repo.save(cargo, order.id)

        if order.route is not None:
            self._segment_repo.save_segments(order.id, order.route.segments)

        event = TrackingEvent(order_id=order.id, status=OrderStatus.CREATED, event_time=order.created_at)
        self._tracking_repo.add_event(event)

        return self._order_to_dto(order)

    def get_order(self, order_id: uuid.UUID) -> OrderResponseDTO:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Заказ {order_id} не найден")
        return self._order_to_dto(order)

    def list_orders_by_sender(self, sender_id: int) -> list[OrderResponseDTO]:
        return [self._order_to_dto(o) for o in self._order_repo.list_by_sender(sender_id)]

    def update_status(self, dto: StatusUpdateDTO) -> OrderResponseDTO:
        order = self._order_repo.get_by_id(dto.order_id)
        if order is None:
            raise OrderNotFoundError(f"Заказ {dto.order_id} не найден")
        new_status = OrderStatus(dto.new_status)
        order.update_status(new_status)
        self._order_repo.update_status(dto.order_id, new_status)
        event = TrackingEvent(
            order_id=dto.order_id, status=new_status,
            event_time=datetime.now(), location_id=dto.location_id, comment=dto.comment,
        )
        self._tracking_repo.add_event(event)
        return self._order_to_dto(order)

    def get_tracking_history(self, order_id: uuid.UUID) -> list[TrackingEventDTO]:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Заказ {order_id} не найден")
        events = self._tracking_repo.get_by_order_id(order_id)
        return [
            TrackingEventDTO(
                status=e.status.value if isinstance(e.status, OrderStatus) else e.status,
                event_time=e.event_time, comment=e.comment,
            )
            for e in events
        ]

    def calculate_route(
        self,
        origin_id: int,
        dest_id: int,
        weight_kg: float,
        volume_m3: float,
        is_fragile: bool = False,
        is_dangerous: bool = False,
        is_liquid: bool = False,
        is_perishable: bool = False,
        is_crushable: bool = False,
        req_temp_control: bool = False,
        strategy_name: str = "cheapest",
    ) -> RouteResponseDTO:
        strategy = _STRATEGIES.get(strategy_name, CheapestRouteStrategy)()
        if self._strategy and strategy_name not in _STRATEGIES:
            strategy = self._strategy

        origin = self._location_repo.get_by_id(origin_id)
        if origin is None:
            raise RouteNotFoundError(f"Локация id={origin_id} не найдена")
        destination = self._location_repo.get_by_id(dest_id)
        if destination is None:
            raise RouteNotFoundError(f"Локация id={dest_id} не найдена")

        if self._graph is None:
            self.build_graph()

        cargo = Cargo(
            weight_kg=weight_kg, volume_m3=volume_m3,
            is_fragile=is_fragile, is_dangerous=is_dangerous,
            is_liquid=is_liquid, is_perishable=is_perishable,
            is_crushable=is_crushable, req_temp_control=req_temp_control,
        )

        route = strategy.calculate_route(self._graph, origin, destination, cargo)

        segment_dtos = [
            RouteSegmentDTO(
                from_location=seg.link.source.name,
                to_location=seg.link.target.name,
                transport_type=(
                    seg.link.transport_type.value
                    if isinstance(seg.link.transport_type, TransportType)
                    else seg.link.transport_type
                ),
                duration_min=seg.link.duration_min,
                cost=seg.link.cost_base,
            )
            for seg in route.segments
        ]

        return RouteResponseDTO(
            segments=segment_dtos,
            total_cost=route.total_cost,
            total_time_min=route.total_time_min,
            estimated_arrival=route.estimated_arrival,
        )