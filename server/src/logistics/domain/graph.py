"""Транспортный граф (вершины = Location, рёбра = TransportLink)."""

from __future__ import annotations

from logistics.domain.models import Location, TransportLink


class TransportGraph:
    """Взвешенный ориентированный граф транспортной сети."""

    def __init__(self) -> None:
        self._nodes: dict[int, Location] = {}
        self._adjacency: dict[int, list[TransportLink]] = {}

    # ── Мутации ───────────────────────────────────────────────────────

    def add_node(self, location: Location) -> None:
        """Добавить вершину в граф."""
        node_id = location.id
        self._nodes[node_id] = location
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []

    def add_edge(self, link: TransportLink) -> None:
        """Добавить ориентированное ребро в граф."""
        source_id = link.source.id
        if source_id not in self._adjacency:
            self._adjacency[source_id] = []
        self._adjacency[source_id].append(link)

    # ── Запросы ───────────────────────────────────────────────────────

    def get_neighbors(self, location: Location) -> list[TransportLink]:
        """Все исходящие рёбра из вершины *location*."""
        return list(self._adjacency.get(location.id, []))

    def get_node_by_id(self, node_id: int) -> Location | None:
        """Найти вершину по ID."""
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> list[Location]:
        """Все вершины графа."""
        return list(self._nodes.values())

    def get_all_edges(self) -> list[TransportLink]:
        """Все рёбра графа."""
        edges: list[TransportLink] = []
        for edge_list in self._adjacency.values():
            edges.extend(edge_list)
        return edges

    @property
    def node_count(self) -> int:
        """Количество вершин."""
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        """Количество рёбер."""
        return sum(len(el) for el in self._adjacency.values())