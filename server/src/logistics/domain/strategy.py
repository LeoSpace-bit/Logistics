"""Паттерн Strategy — алгоритмы расчёта маршрута."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.logistics.domain.graph import TransportGraph
from src.logistics.domain.models import Cargo, Location, Route


class IRouteStrategy(ABC):
    """Абстрактная стратегия расчёта маршрута (интерфейс).

    Конкретные реализации подставляются в :class:`LogisticsService`
    через ``set_strategy()``.
    """

    @abstractmethod
    def calculate_route(
        self,
        graph: TransportGraph,
        origin: Location,
        destination: Location,
        cargo: Cargo,
    ) -> Route:
        """Найти оптимальный маршрут в графе.

        Args:
            graph: Транспортный граф.
            origin: Точка отправления.
            destination: Точка назначения.
            cargo: Описание груза (для фильтрации рёбер).

        Returns:
            Рассчитанный маршрут.

        Raises:
            RouteNotFoundError: маршрут не существует.
            CargoRestrictionError: ни одно ребро не допускает данный груз.
        """
        ...


class CheapestRouteStrategy(IRouteStrategy):
    """Поиск самого дешёвого маршрута (Dijkstra по ``cost_base``)."""

    def calculate_route(
        self,
        graph: TransportGraph,
        origin: Location,
        destination: Location,
        cargo: Cargo,
    ) -> Route:
        raise NotImplementedError


class FastestRouteStrategy(IRouteStrategy):
    """Поиск самого быстрого маршрута (Dijkstra по ``duration_min``)."""

    def calculate_route(
        self,
        graph: TransportGraph,
        origin: Location,
        destination: Location,
        cargo: Cargo,
    ) -> Route:
        raise NotImplementedError