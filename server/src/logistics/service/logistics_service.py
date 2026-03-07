"""Главный сервис — с логированием и полной персистенцией."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from logistics.domain.builder import CargoBuilder
from logistics.domain.enums import OrderStatus, TransportType, UserRole
from logistics.domain.exceptions import (
    AuthenticationError,
    DomainError,
    OrderNotFoundError,
    RouteNotFoundError,
)
from logistics.domain.graph import TransportGraph
from logistics.domain.models import Cargo, Order, TrackingEvent, User
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

logger = logging.getLogger("logistics.service")

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
        session: Session | None = None,
    ) -> None:
        self._order_repo = order_repo
        self._cargo_repo = cargo_repo
        self._location_repo = location_repo
        self._link_repo = link_repo
        self._tracking_repo = tracking_repo
        self._segment_repo = segment_repo
        self._user_repo = user_repo
        self._session = session
        self._strategy: IRouteStrategy | None = None
        self._graph: TransportGraph | None = None

    def _commit(self) -> None:
        if self._session is not None:
            self._session.commit()
            logger.debug("Транзакция зафиксирована")

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

    # ── Аутентификация ────────────────────────────────────────────────

    def authenticate(self, login: str, password: str) -> dict:
        user = self._user_repo.get_by_login(login)
        if user is None or user.password_hash != password:
            raise AuthenticationError("Неверный логин или пароль")
        logger.info("Вход: %s (role=%s)", user.login, user.role)
        return {
            "id": user.id,
            "login": user.login,
            "role": user.role.value if isinstance(user.role, UserRole) else user.role,
            "full_name": user.full_name or user.login,
        }

    def register_user(self, login: str, password: str, full_name: str) -> dict:
        if self._user_repo.get_by_login(login) is not None:
            raise DomainError(f"Логин «{login}» уже занят")
        user = User(login=login, password_hash=password, role=UserRole.CLIENT, full_name=full_name)
        self._user_repo.save(user)
        self._commit()
        logger.info("Регистрация: %s (id=%s)", user.login, user.id)
        return {
            "id": user.id, "login": user.login,
            "role": user.role.value, "full_name": user.full_name,
        }

    # ── Стратегия и граф ──────────────────────────────────────────────

    def set_strategy(self, strategy: IRouteStrategy) -> None:
        self._strategy = strategy

    def build_graph(self) -> TransportGraph:
        graph = TransportGraph()
        locations = self._location_repo.get_all()
        links = self._link_repo.get_all()
        for loc in locations:
            graph.add_node(loc)
        for link in links:
            graph.add_edge(link)
        self._graph = graph
        logger.info("Граф построен: %d вершин, %d рёбер", graph.node_count, graph.edge_count)
        return graph

    # ── Заказы ────────────────────────────────────────────────────────

    def create_order(self, dto: OrderCreateDTO) -> OrderResponseDTO:
        logger.info(
            "Создание заказа: sender=%d, %d→%d, вес=%.1f кг, стратегия=%s",
            dto.sender_id, dto.origin_location_id, dto.dest_location_id,
            dto.cargo.weight_kg, dto.strategy,
        )

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
        cargo = builder.build()
        logger.debug("Груз собран: %.1f кг, %.4f м³", cargo.weight_kg, cargo.volume_m3)

        receiver = None
        if dto.receiver_id is not None:
            receiver = self._user_repo.get_by_id(dto.receiver_id)

        order = Order(
            sender=sender, origin=origin, destination=destination,
            cargo=cargo, receiver=receiver,
        )

        # ── Расчёт маршрута ──────────────────────────────────────────
        route_warning: str | None = None
        strategy = self._strategy
        if dto.strategy and dto.strategy in _STRATEGIES:
            strategy = _STRATEGIES[dto.strategy]()

        if strategy is not None:
            if self._graph is None:
                self.build_graph()
            try:
                route = strategy.calculate_route(self._graph, origin, destination, cargo)
                order.assign_route(route)
                logger.info(
                    "Маршрут рассчитан: %d сегм., стоимость=%s, время=%d мин",
                    len(route.segments), route.total_cost, route.total_time_min,
                )
            except RouteNotFoundError as e:
                route_warning = str(e)
                logger.warning("⚠️ Маршрут не найден: %s", e)

        # ── Сохранение ────────────────────────────────────────────────
        self._order_repo.save(order)
        self._cargo_repo.save(cargo, order.id)

        if order.route is not None and order.route.segments:
            self._segment_repo.save_segments(order.id, order.route.segments)
            logger.debug("Сохранено %d сегментов маршрута", len(order.route.segments))

        event = TrackingEvent(
            order_id=order.id, status=OrderStatus.CREATED,
            event_time=order.created_at,
            comment=route_warning,  # записываем причину в историю
        )
        self._tracking_repo.add_event(event)
        self._commit()

        logger.info("✅ Заказ создан: %s, стоимость=%s", order.id, order.total_cost)

        result = self._order_to_dto(order)
        # Прокидываем предупреждение (серверный dispatch его подхватит)
        result._route_warning = route_warning  # type: ignore[attr-defined]
        return result

    def get_order(self, order_id: uuid.UUID) -> OrderResponseDTO:
        order = self._order_repo.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(f"Заказ {order_id} не найден")
        return self._order_to_dto(order)

    def list_orders_by_sender(self, sender_id: int) -> list[OrderResponseDTO]:
        return [self._order_to_dto(o) for o in self._order_repo.list_by_sender(sender_id)]

    def list_all_orders(self) -> list[OrderResponseDTO]:
        return [self._order_to_dto(o) for o in self._order_repo.list_all()]

    # ── Маршрут заказа ────────────────────────────────────────────────

    def get_order_route(self, order_id: uuid.UUID) -> list[RouteSegmentDTO]:
        """Получить сохранённые сегменты маршрута заказа."""
        segments = self._segment_repo.get_by_order_id(order_id)
        return [
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
            for seg in segments
        ]

    # ── Статус ────────────────────────────────────────────────────────

    def update_status(self, dto: StatusUpdateDTO) -> OrderResponseDTO:
        order = self._order_repo.get_by_id(dto.order_id)
        if order is None:
            raise OrderNotFoundError(f"Заказ {dto.order_id} не найден")

        new_status = OrderStatus(dto.new_status)
        logger.info(
            "Обновление статуса: %s  %s → %s (force=%s)",
            dto.order_id, order.status.value, new_status.value, dto.force,
        )

        order.update_status(new_status, force=dto.force)
        self._order_repo.update_status(dto.order_id, new_status)

        event = TrackingEvent(
            order_id=dto.order_id, status=new_status,
            event_time=datetime.now(), location_id=dto.location_id,
            comment=dto.comment,
        )
        self._tracking_repo.add_event(event)
        self._commit()

        logger.info("✅ Статус обновлён: %s → %s", dto.order_id, new_status.value)
        return self._order_to_dto(order)

    # ── Отслеживание ──────────────────────────────────────────────────

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

    # ── Расчёт маршрута ───────────────────────────────────────────────

    def calculate_route(
        self,
        origin_id: int, dest_id: int,
        weight_kg: float, volume_m3: float,
        is_fragile: bool = False, is_dangerous: bool = False,
        is_liquid: bool = False, is_perishable: bool = False,
        is_crushable: bool = False, req_temp_control: bool = False,
        strategy_name: str = "cheapest",
    ) -> RouteResponseDTO:
        logger.info(
            "Расчёт маршрута: %d→%d, %.1f кг, %.3f м³, стратегия=%s",
            origin_id, dest_id, weight_kg, volume_m3, strategy_name,
        )

        strategy = _STRATEGIES.get(strategy_name, CheapestRouteStrategy)()

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

        logger.info(
            "✅ Маршрут найден: %d сегм., стоимость=%s, время=%d мин",
            len(route.segments), route.total_cost, route.total_time_min,
        )

        return RouteResponseDTO(
            segments=[
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
            ],
            total_cost=route.total_cost,
            total_time_min=route.total_time_min,
            estimated_arrival=route.estimated_arrival,
        )