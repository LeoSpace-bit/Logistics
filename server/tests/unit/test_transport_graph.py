"""Тесты TransportGraph — управление вершинами и рёбрами графа."""

import pytest
from decimal import Decimal

from logistics.domain.enums import NodeType, TransportType
from logistics.domain.graph import TransportGraph
from logistics.domain.models import Location, TransportLink


class TestGraphAddNode:
    """TransportGraph.add_node()."""

    def test_add_single_node(
        self, sample_location_moscow: Location,
    ) -> None:
        """Добавление одной вершины увеличивает node_count."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        assert graph.node_count == 1

    def test_add_multiple_nodes(
        self,
        sample_location_moscow: Location,
        sample_location_spb: Location,
    ) -> None:
        """Добавление двух вершин → node_count == 2."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        graph.add_node(sample_location_spb)
        assert graph.node_count == 2

    def test_get_node_by_id(
        self, sample_location_moscow: Location,
    ) -> None:
        """Поиск добавленной вершины по ID."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        found = graph.get_node_by_id(sample_location_moscow.id)
        assert found is not None
        assert found.name == "Москва-Склад"

    def test_get_nonexistent_node_returns_none(self) -> None:
        """Поиск несуществующей вершины → None."""
        graph = TransportGraph()
        assert graph.get_node_by_id(999) is None

    def test_get_all_nodes(
        self,
        sample_location_moscow: Location,
        sample_location_spb: Location,
    ) -> None:
        """get_all_nodes() возвращает все вершины."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        graph.add_node(sample_location_spb)
        nodes = graph.get_all_nodes()
        assert len(nodes) == 2


class TestGraphAddEdge:
    """TransportGraph.add_edge()."""

    def test_add_edge_increases_count(
        self,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_link: TransportLink,
    ) -> None:
        """Добавление ребра увеличивает edge_count."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        graph.add_node(sample_location_spb)
        graph.add_edge(sample_link)
        assert graph.edge_count == 1

    def test_get_all_edges(
        self,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_link: TransportLink,
        air_link: TransportLink,
    ) -> None:
        """get_all_edges() возвращает все рёбра."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        graph.add_node(sample_location_spb)
        graph.add_edge(sample_link)
        graph.add_edge(air_link)
        assert len(graph.get_all_edges()) == 2


class TestGraphGetNeighbors:
    """TransportGraph.get_neighbors()."""

    def test_neighbors_of_source(
        self,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_link: TransportLink,
    ) -> None:
        """У Москвы есть исходящее ребро в СПб."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        graph.add_node(sample_location_spb)
        graph.add_edge(sample_link)
        neighbors = graph.get_neighbors(sample_location_moscow)
        assert len(neighbors) == 1
        assert neighbors[0].target.name == "СПб-ПВЗ"

    def test_no_neighbors_for_sink(
        self,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_link: TransportLink,
    ) -> None:
        """У СПб нет исходящих рёбер → пустой список."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        graph.add_node(sample_location_spb)
        graph.add_edge(sample_link)
        assert graph.get_neighbors(sample_location_spb) == []

    def test_multiple_neighbors(
        self,
        sample_location_moscow: Location,
        sample_location_spb: Location,
        sample_link: TransportLink,
        air_link: TransportLink,
    ) -> None:
        """Два ребра из одной вершины → 2 соседа."""
        graph = TransportGraph()
        graph.add_node(sample_location_moscow)
        graph.add_node(sample_location_spb)
        graph.add_edge(sample_link)
        graph.add_edge(air_link)
        neighbors = graph.get_neighbors(sample_location_moscow)
        assert len(neighbors) == 2


class TestGraphEdgeCases:
    """Граничные случаи."""

    def test_empty_graph_node_count(self) -> None:
        """Пустой граф — 0 вершин."""
        graph = TransportGraph()
        assert graph.node_count == 0

    def test_empty_graph_edge_count(self) -> None:
        """Пустой граф — 0 рёбер."""
        graph = TransportGraph()
        assert graph.edge_count == 0

    def test_empty_graph_get_all_nodes(self) -> None:
        """Пустой граф — пустой список вершин."""
        graph = TransportGraph()
        assert graph.get_all_nodes() == []

    def test_empty_graph_get_all_edges(self) -> None:
        """Пустой граф — пустой список рёбер."""
        graph = TransportGraph()
        assert graph.get_all_edges() == []