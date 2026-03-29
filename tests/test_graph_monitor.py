"""Tests for Graph Monitor"""

import pytest

from orchestration.graph_monitor import (
    GraphMetrics,
    NodeMetrics,
    GraphMonitor,
    GraphAnalyzer,
    GraphVisualizer,
    GraphValidator,
    get_graph_monitor,
)


class TestGraphMetrics:
    """Test GraphMetrics"""

    def test_creation(self):
        """Test creation"""
        metrics = GraphMetrics(node_count=5, edge_count=10)
        assert metrics.node_count == 5
        assert metrics.edge_count == 10


class TestNodeMetrics:
    """Test NodeMetrics"""

    def test_creation(self):
        """Test creation"""
        metrics = NodeMetrics(node_id="a", degree=3)
        assert metrics.node_id == "a"
        assert metrics.degree == 3


class TestGraphMonitor:
    """Test GraphMonitor"""

    @pytest.fixture
    def monitor(self):
        """Create monitor"""
        return GraphMonitor()

    def test_creation(self, monitor):
        """Test creation"""
        assert monitor is not None

    def test_record_snapshot(self, monitor):
        """Test record snapshot"""
        monitor.record_snapshot(5, 10)
        history = monitor.get_history()
        assert len(history) == 1
        assert history[0]["node_count"] == 5

    def test_get_growth_rate(self, monitor):
        """Test get growth rate"""
        import time
        monitor.record_snapshot(5, 10)
        time.sleep(0.1)
        monitor.record_snapshot(10, 20)
        rate = monitor.get_growth_rate()
        assert rate >= 0


class TestGraphAnalyzer:
    """Test GraphAnalyzer"""

    def test_calculate_density(self):
        """Test calculate density"""
        density = GraphAnalyzer.calculate_density(5, 10)
        assert density > 0

    def test_calculate_avg_degree(self):
        """Test calculate avg degree"""
        avg = GraphAnalyzer.calculate_avg_degree(10, 5)
        assert avg == 4.0

    def test_get_degree_distribution(self):
        """Test degree distribution"""
        adjacency = {
            "a": [("b", 1), ("c", 1)],
            "b": [("a", 1)],
            "c": [("a", 1)],
        }
        dist = GraphAnalyzer.get_degree_distribution(adjacency)
        assert 2 in dist

    def test_find_articulation_points(self):
        """Test find articulation points"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("a", 1), ("c", 1)],
            "c": [("b", 1)],
        }
        ap = GraphAnalyzer.find_articulation_points(adjacency, "a")
        assert "b" in ap

    def test_find_bridges(self):
        """Test find bridges"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("a", 1), ("c", 1)],
            "c": [("b", 1)],
        }
        bridges = GraphAnalyzer.find_bridges(adjacency)
        assert len(bridges) > 0

    def test_calculate_pagerank(self):
        """Test calculate pagerank"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("c", 1)],
            "c": [("a", 1)],
        }
        pr = GraphAnalyzer.calculate_pagerank(adjacency, iterations=10)
        assert "a" in pr
        assert all(0 <= v <= 1 for v in pr.values())

    def test_calculate_closeness_centrality(self):
        """Test closeness centrality"""
        adjacency = {
            "a": [("b", 1), ("c", 1)],
            "b": [("a", 1), ("c", 1)],
            "c": [("a", 1), ("b", 1)],
        }
        closeness = GraphAnalyzer.calculate_closeness_centrality(adjacency, "a")
        assert closeness > 0


class TestGraphVisualizer:
    """Test GraphVisualizer"""

    def test_to_dot_directed(self):
        """Test to dot directed"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("c", 1)],
        }
        dot = GraphVisualizer.to_dot(adjacency, directed=True)
        assert "digraph" in dot
        assert "->" in dot

    def test_to_dot_undirected(self):
        """Test to dot undirected"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("a", 1)],
        }
        dot = GraphVisualizer.to_dot(adjacency, directed=False)
        assert "graph" in dot
        assert "--" in dot

    def test_to_adjacency_matrix(self):
        """Test to adjacency matrix"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("a", 1)],
        }
        matrix = GraphVisualizer.to_adjacency_matrix(adjacency)
        assert "a" in matrix
        assert matrix["a"]["b"] == 1

    def test_to_edge_list(self):
        """Test to edge list"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("a", 1)],
        }
        edges = GraphVisualizer.to_edge_list(adjacency)
        assert len(edges) == 1


class TestGraphValidator:
    """Test GraphValidator"""

    def test_is_valid_node(self):
        """Test is valid node"""
        assert GraphValidator.is_valid_node("a") is True
        assert GraphValidator.is_valid_node("") is False

    def test_is_valid_edge(self):
        """Test is valid edge"""
        assert GraphValidator.is_valid_edge("a", "b") is True
        assert GraphValidator.is_valid_edge("a", "a") is False
        assert GraphValidator.is_valid_edge("a", "b", -1) is False

    def test_validate_graph(self):
        """Test validate graph"""
        adjacency = {
            "a": [("b", 1)],
            "b": [("a", 1)],
        }
        valid, errors = GraphValidator.validate_graph(adjacency)
        assert valid is True
        assert len(errors) == 0


class TestGetGraphMonitor:
    """Test singleton"""

    def test_singleton(self):
        """Test singleton"""
        m1 = get_graph_monitor()
        m2 = get_graph_monitor()
        assert m1 is m2
