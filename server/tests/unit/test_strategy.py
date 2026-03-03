"""Тесты паттерна Strategy — алгоритмы расчёта маршрута."""

from decimal import Decimal

import pytest

from logistics.domain.exceptions import CargoRestrictionError, RouteNotFoundError
from logistics.domain.graph import TransportGraph
from logistics.domain.models import Cargo, Location, Route
from logistics.domain.strategy import (
    CheapestRouteStrategy,
    FastestRouteStrategy,
    IRouteStrategy,
)


class TestCheapestRouteStrategy:
    """CheapestRouteStrategy — самый дешёвый маршрут."""

    def test_implements_interface(self) -> None:
        """CheapestRouteStrategy наследует IRouteStrategy."""
        assert issubclass(CheapestRouteStrategy, IRouteStrategy)

    def test_returns_route(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Метод возвращает объект Route."""
        strategy = CheapestRouteStrategy()
        route = strategy.calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        assert isinstance(route, Route)

    def test_cheapest_is_cheaper_than_fastest(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Дешёвый маршрут стоит не дороже быстрого."""
        cheapest = CheapestRouteStrategy().calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        fastest = FastestRouteStrategy().calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        assert cheapest.total_cost <= fastest.total_cost

    def test_route_has_segments(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Маршрут содержит хотя бы один сегмент."""
        strategy = CheapestRouteStrategy()
        route = strategy.calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        assert len(route.segments) >= 1

    def test_route_total_cost_positive(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Стоимость маршрута > 0."""
        strategy = CheapestRouteStrategy()
        route = strategy.calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        assert route.total_cost > 0

    def test_no_route_raises(
        self,
        sample_location_moscow: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Маршрут не существует → RouteNotFoundError."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        isolated = Location(
            id=99, name="Остров", type="WAREHOUSE", address="Нигде",
        )
        graph.add_node(isolated)
        strategy = CheapestRouteStrategy()
        with pytest.raises(RouteNotFoundError):
            strategy.calculate_route(
                graph, sample_location_moscow, isolated, sample_cargo,
            )


class TestFastestRouteStrategy:
    """FastestRouteStrategy — самый быстрый маршрут."""

    def test_implements_interface(self) -> None:
        """FastestRouteStrategy наследует IRouteStrategy."""
        assert issubclass(FastestRouteStrategy, IRouteStrategy)

    def test_returns_route(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Метод возвращает объект Route."""
        strategy = FastestRouteStrategy()
        route = strategy.calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        assert isinstance(route, Route)

    def test_fastest_is_faster_than_cheapest(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Быстрый маршрут не медленнее дешёвого."""
        cheapest = CheapestRouteStrategy().calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        fastest = FastestRouteStrategy().calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        assert fastest.total_time_min <= cheapest.total_time_min

    def test_route_total_time_positive(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Время маршрута > 0."""
        strategy = FastestRouteStrategy()
        route = strategy.calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        assert route.total_time_min > 0

    def test_no_route_raises(
        self,
        sample_location_moscow: Location,
        sample_cargo: Cargo,
    ) -> None:
        """Маршрут не существует → RouteNotFoundError."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        isolated = Location(
            id=99, name="Остров", type="WAREHOUSE", address="Нигде",
        )
        graph.add_node(isolated)
        strategy = FastestRouteStrategy()
        with pytest.raises(RouteNotFoundError):
            strategy.calculate_route(
                graph, sample_location_moscow, isolated, sample_cargo,
            )


class TestStrategySegmentOrder:
    """Проверка порядка сегментов в маршруте."""

    def test_segments_ordered_by_sequence(
        self,
        triangle_graph: TransportGraph,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_cargo: Cargo,
    ) -> None:
        """step_sequence идёт по возрастанию."""
        strategy = CheapestRouteStrategy()
        route = strategy.calculate_route(
            triangle_graph,
            sample_location_moscow,
            sample_location_spb,
            sample_cargo,
        )
        sequences = [s.step_sequence for s in route.segments]
        assert sequences == sorted(sequences)