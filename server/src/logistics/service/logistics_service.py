"""Главный сервис приложения — оркестрация бизнес-логики."""

from __future__ import annotations

import uuid

from src.logistics.domain.graph import TransportGraph
from src.logistics.domain.strategy import IRouteStrategy
from src.logistics.infrastructure.repositories import (
    ICargoRepository,
    ILocationRepository,
    IOrderRepository,
    IRouteSegmentRepository,
    ITrackingRepository,
    ITransportLinkRepository,
    IUserRepository,
)
from src.logistics.service.dto import (
    OrderCreateDTO,
    OrderResponseDTO,
    RouteResponseDTO,
    StatusUpdateDTO,
    TrackingEventDTO,
)


class LogisticsService:
    """Сервис логистики.

    Координирует работу репозиториев, строителя, стратегии и
    транспортного графа для выполнения пользовательских сценариев.
    """

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

    # ── Стратегия и граф ──────────────────────────────────────────────

    def set_strategy(self, strategy: IRouteStrategy) -> None:
        """Установить стратегию расчёта маршрута.

        Args:
            strategy: Реализация IRouteStrategy (Cheapest / Fastest).
        """
        raise NotImplementedError

    def build_graph(self) -> TransportGraph:
        """Построить транспортный граф из данных репозиториев.

        Returns:
            Заполненный TransportGraph.
        """
        raise NotImplementedError

    # ── Управление заказами ───────────────────────────────────────────

    def create_order(self, dto: OrderCreateDTO) -> OrderResponseDTO:
        """Создать заказ.

        Шаги:
        1. Валидировать входные данные.
        2. Собрать Cargo через CargoBuilder.
        3. Рассчитать маршрут (если стратегия установлена).
        4. Сохранить Order, Cargo и сегменты маршрута.
        5. Записать событие CREATED в tracking_history.

        Args:
            dto: Данные нового заказа.

        Returns:
            DTO с информацией о созданном заказе.

        Raises:
            InvalidCargoError: некорректный груз.
            RouteNotFoundError: маршрут не найден.
            OrderNotFoundError: отправитель / локации не найдены.
        """
        raise NotImplementedError

    def get_order(self, order_id: uuid.UUID) -> OrderResponseDTO:
        """Получить информацию о заказе по ID.

        Args:
            order_id: UUID заказа.

        Returns:
            DTO заказа.

        Raises:
            OrderNotFoundError: заказ не найден.
        """
        raise NotImplementedError

    def list_orders_by_sender(
        self, sender_id: int,
    ) -> list[OrderResponseDTO]:
        """Список заказов конкретного отправителя.

        Args:
            sender_id: ID пользователя-отправителя.

        Returns:
            Список DTO заказов (может быть пустым).
        """
        raise NotImplementedError

    # ── Управление статусом ───────────────────────────────────────────

    def update_status(self, dto: StatusUpdateDTO) -> OrderResponseDTO:
        """Обновить статус заказа.

        Шаги:
        1. Проверить существование заказа.
        2. Валидировать переход статуса.
        3. Обновить статус в orders.
        4. Записать событие в tracking_history.

        Args:
            dto: Данные обновления статуса.

        Returns:
            DTO с обновлённым заказом.

        Raises:
            OrderNotFoundError: заказ не найден.
            InvalidStatusTransitionError: переход статуса не разрешён.
        """
        raise NotImplementedError

    # ── Отслеживание ──────────────────────────────────────────────────

    def get_tracking_history(
        self, order_id: uuid.UUID,
    ) -> list[TrackingEventDTO]:
        """Получить журнал событий заказа.

        Args:
            order_id: UUID заказа.

        Returns:
            Упорядоченный по времени список событий.

        Raises:
            OrderNotFoundError: заказ не найден.
        """
        raise NotImplementedError

    # ── Маршрут и стоимость ───────────────────────────────────────────

    def calculate_route(
        self,
        origin_id: int,
        dest_id: int,
        weight_kg: float,
        volume_m3: float,
        is_fragile: bool = False,
        is_dangerous: bool = False,
    ) -> RouteResponseDTO:
        """Рассчитать маршрут и стоимость (предварительная оценка).

        Не создаёт заказ, только считает.

        Args:
            origin_id: ID точки отправления.
            dest_id: ID точки назначения.
            weight_kg: Вес груза (кг).
            volume_m3: Объём груза (м³).
            is_fragile: Хрупкий ли груз.
            is_dangerous: Опасный ли груз.

        Returns:
            DTO с маршрутом, стоимостью и временем.

        Raises:
            RouteNotFoundError: маршрут не найден.
        """
        raise NotImplementedError