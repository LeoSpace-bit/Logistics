"""Транспортный граф (вершины = Location, рёбра = TransportLink)."""

from __future__ import annotations

from src.logistics.domain.models import Location, TransportLink


class TransportGraph:
    """Взвешенный ориентированный граф транспортной сети.

    Используется стратегиями (:class:`IRouteStrategy`) для
    расчёта маршрутов.
    """

    def __init__(self) -> None:
        self._nodes: dict[int, Location] = {}
        self._adjacency: dict[int, list[TransportLink]] = {}

    # ── Мутации ───────────────────────────────────────────────────────

    def add_node(self, location: Location) -> None:
        """Добавить вершину в граф.

        Args:
            location: Объект Location (id не должен быть None).
        """
        raise NotImplementedError

    def add_edge(self, link: TransportLink) -> None:
        """Добавить ориентированное ребро в граф.

        Args:
            link: Объект TransportLink (source и target должны уже быть в графе).
        """
        raise NotImplementedError

    # ── Запросы ───────────────────────────────────────────────────────

    def get_neighbors(self, location: Location) -> list[TransportLink]:
        """Все исходящие рёбра из вершины *location*.

        Returns:
            Список рёбер; пустой, если вершина — тупик.
        """
        raise NotImplementedError

    def get_node_by_id(self, node_id: int) -> Location | None:
        """Найти вершину по ID.

        Returns:
            Location или None, если не найдена.
        """
        raise NotImplementedError

    def get_all_nodes(self) -> list[Location]:
        """Все вершины графа."""
        raise NotImplementedError

    def get_all_edges(self) -> list[TransportLink]:
        """Все рёбра графа."""
        raise NotImplementedError

    @property
    def node_count(self) -> int:
        """Количество вершин."""
        raise NotImplementedError

    @property
    def edge_count(self) -> int:
        """Количество рёбер."""
        raise NotImplementedError