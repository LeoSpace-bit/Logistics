"""Паттерн Strategy — Dijkstra по стоимости / времени."""

from __future__ import annotations

import heapq
from abc import ABC, abstractmethod
from decimal import Decimal

from logistics.domain.exceptions import RouteNotFoundError
from logistics.domain.graph import TransportGraph
from logistics.domain.models import (
    Cargo,
    Location,
    Route,
    RouteSegment,
    TransportLink,
)


class IRouteStrategy(ABC):

    @abstractmethod
    def calculate_route(
        self,
        graph: TransportGraph,
        origin: Location,
        destination: Location,
        cargo: Cargo,
    ) -> Route: ...


class _DijkstraBase(IRouteStrategy):
    """Базовый класс Dijkstra с настраиваемой весовой функцией."""

    def _edge_weight(self, link: TransportLink) -> float:
        raise NotImplementedError

    def calculate_route(
        self,
        graph: TransportGraph,
        origin: Location,
        destination: Location,
        cargo: Cargo,
    ) -> Route:
        if origin.id == destination.id:
            return Route()

        dist: dict[int, float] = {origin.id: 0.0}
        prev: dict[int, tuple[TransportLink, int]] = {}
        visited: set[int] = set()
        heap: list[tuple[float, int]] = [(0.0, origin.id)]

        while heap:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)

            if u == destination.id:
                break

            node = graph.get_node_by_id(u)
            if node is None:
                continue

            for link in graph.get_neighbors(node):
                if not link.can_transport(cargo):
                    continue
                v = link.target.id
                w = self._edge_weight(link)
                new_dist = d + w
                if v not in dist or new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = (link, u)
                    heapq.heappush(heap, (new_dist, v))

        if destination.id not in visited:
            # Собираем причины отказа для информативного сообщения
            reasons = self._collect_rejection_reasons(graph, origin, cargo)
            msg = f"Маршрут из «{origin.name}» в «{destination.name}» не найден"
            if reasons:
                msg += ". Ограничения: " + "; ".join(reasons)
            raise RouteNotFoundError(msg)

        # Восстановление пути
        path_links: list[TransportLink] = []
        current = destination.id
        while current in prev:
            link, prev_node = prev[current]
            path_links.append(link)
            current = prev_node
        path_links.reverse()

        segments: list[RouteSegment] = []
        total_cost = Decimal("0")
        total_time = 0
        for i, link in enumerate(path_links):
            segments.append(RouteSegment(link=link, step_sequence=i + 1))
            total_cost += link.cost_base
            total_time += link.duration_min

        return Route(
            segments=segments,
            total_cost=total_cost,
            total_time_min=total_time,
        )

    @staticmethod
    def _collect_rejection_reasons(
        graph: TransportGraph,
        origin: Location,
        cargo: Cargo,
    ) -> list[str]:
        """Собрать человекочитаемые причины, почему рёбра отклоняют груз."""
        reasons: set[str] = set()
        for link in graph.get_all_edges():
            if link.can_transport(cargo):
                continue
            if link.max_weight_kg and cargo.weight_kg > link.max_weight_kg:
                reasons.add(f"вес {cargo.weight_kg} кг > лимит {link.max_weight_kg} кг")
            if link.max_volume_m3 and cargo.volume_m3 > link.max_volume_m3:
                reasons.add(f"объём {cargo.volume_m3} м³ > лимит {link.max_volume_m3} м³")
            if cargo.is_dangerous and not link.allows_dangerous:
                reasons.add(f"{link.transport_type.value} не перевозит опасные грузы")
            if cargo.is_fragile and not link.allows_fragile:
                reasons.add(f"{link.transport_type.value} не перевозит хрупкие грузы")
            if cargo.is_liquid and not link.allows_liquid:
                reasons.add(f"{link.transport_type.value} не перевозит жидкости")
            if cargo.is_perishable and not link.allows_perishable:
                reasons.add(f"{link.transport_type.value} не перевозит скоропортящееся")
            if cargo.is_crushable and not link.allows_crushable:
                reasons.add(f"{link.transport_type.value} не перевозит мнущееся")
            if cargo.req_temp_control and not link.allows_temp_control:
                reasons.add(f"{link.transport_type.value} не поддерживает тем. контроль")
        return sorted(reasons)


class CheapestRouteStrategy(_DijkstraBase):
    """Dijkstra по ``cost_base``."""

    def _edge_weight(self, link: TransportLink) -> float:
        return float(link.cost_base)


class FastestRouteStrategy(_DijkstraBase):
    """Dijkstra по ``duration_min``."""

    def _edge_weight(self, link: TransportLink) -> float:
        return float(link.duration_min)