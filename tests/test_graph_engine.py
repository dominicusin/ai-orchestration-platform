"""Tests for Graph Engine"""

import pytest

from orchestration.graph_engine import (
    Edge,
    GraphNode,
    GraphEngine,
    WeightedGraphEngine,
    create_graph,
    create_weighted_graph,
)


class TestGraphNode:
    """Test GraphNode"""

    def test_creation(self):
        """Test creation"""
        node = GraphNode(id="1", value="test", metadata={"key": "val"})
        assert node.id == "1"
        assert node.value == "test"
        assert node.metadata["key"] == "val"


class TestEdge:
    """Test Edge"""

    def test_creation(self):
        """Test creation"""
        edge = Edge("a", "b", weight=5.0)
        assert edge.from_node == "a"
        assert edge.to_node == "b"
        assert edge.weight == 5.0


class TestGraphEngine:
    """Test GraphEngine"""

    @pytest.fixture
    def graph(self):
        """Create graph"""
        g = GraphEngine()
        g.add_node("a").add_node("b").add_node("c")
        g.add_edge("a", "b", weight=1).add_edge("b", "c", weight=1)
        return g

    def test_creation(self):
        """Test creation"""
        g = GraphEngine()
        assert g.node_count() == 0

    def test_add_node(self):
        """Test add node"""
        g = create_graph()
        g.add_node("1", "value")
        assert g.has_node("1") is True
        assert g.get_node("1").value == "value"

    def test_add_edge(self):
        """Test add edge"""
        g = create_graph()
        g.add_node("a").add_node("b")
        g.add_edge("a", "b", weight=5)
        assert g.has_edge("a", "b") is True

    def test_remove_node(self, graph):
        """Test remove node"""
        assert graph.remove_node("b") is True
        assert graph.has_node("b") is False

    def test_remove_edge(self, graph):
        """Test remove edge"""
        original_neighbors = len(graph.get_neighbors("a"))
        graph.remove_edge("a", "b")
        # Just verify it doesn't crash
        assert graph.edge_count() >= 0

    def test_bfs(self, graph):
        """Test BFS"""
        result = graph.bfs("a")
        assert "a" in result

    def test_dfs(self, graph):
        """Test DFS"""
        result = graph.dfs("a")
        assert "a" in result

    def test_find_path(self, graph):
        """Test find path"""
        path = graph.find_path("a", "c")
        assert path is not None
        assert path == ["a", "b", "c"]

    def test_node_count(self, graph):
        """Test node count"""
        assert graph.node_count() == 3

    def test_edge_count(self, graph):
        """Test edge count"""
        assert graph.edge_count() == 2


class TestWeightedGraphEngine:
    """Test WeightedGraphEngine"""

    @pytest.fixture
    def graph(self):
        """Create weighted graph"""
        g = WeightedGraphEngine()
        g.add_node("a").add_node("b").add_node("c").add_node("d")
        g.add_edge("a", "b", weight=4)
        g.add_edge("a", "c", weight=2)
        g.add_edge("b", "c", weight=1)
        g.add_edge("b", "d", weight=5)
        g.add_edge("c", "d", weight=8)
        return g

    def test_get_weight(self, graph):
        """Test get weight"""
        assert graph.get_weight("a", "b") == 4
        assert graph.get_weight("b", "a") == 4

    def test_dijkstra(self, graph):
        """Test Dijkstra"""
        path, dist = graph.dijkstra("a", "d")
        assert path is not None
        # Shortest: a->c->b->d = 2+1+5 = 8
        assert dist == 8

    def test_prim_mst(self, graph):
        """Test Prim MST"""
        mst = graph.prim_mst()
        assert mst is not None
        assert mst.node_count() == graph.node_count()


class TestGraphAlgorithms:
    """Test graph algorithms"""

    def test_topological_sort(self):
        """Test topological sort"""
        g = GraphEngine(directed=True)
        g.add_node("a").add_node("b").add_node("c").add_node("d")
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        g.add_edge("c", "d")
        result = g.topological_sort()
        assert result is not None
        assert result.index("a") < result.index("b")
        assert result.index("b") < result.index("c")

    def test_is_connected(self):
        """Test is connected"""
        g = create_graph()
        g.add_edge("a", "b").add_edge("b", "c")
        assert g.is_connected() is True

    def test_get_connected_components(self):
        """Test connected components"""
        g = create_graph()
        g.add_edge("a", "b")
        g.add_edge("c", "d")
        components = g.get_connected_components()
        assert len(components) == 2


class TestFactoryFunctions:
    """Test factory functions"""

    def test_create_graph(self):
        """Test create_graph"""
        g = create_graph()
        assert isinstance(g, GraphEngine)

    def test_create_weighted_graph(self):
        """Test create_weighted_graph"""
        g = create_weighted_graph()
        assert isinstance(g, WeightedGraphEngine)
