"""Tests for Graph Recursive (DFS/BFS)"""

import pytest

from orchestration.graph_recursive import (
    Node,
    Graph,
    TreeTraversal,
    TreeBuilder,
    create_node,
)


class TestNode:
    """Test Node"""

    def test_creation(self):
        """Test creation"""
        node = Node(id="1", value="test")
        assert node.id == "1"
        assert node.value == "test"
        assert node.is_leaf() is True

    def test_add_child(self):
        """Test add child"""
        parent = Node(id="1")
        child = Node(id="2")
        parent.add_child(child)
        assert len(parent.children) == 1
        assert parent.is_leaf() is False


class TestGraph:
    """Test Graph"""

    def test_creation(self):
        """Test creation"""
        graph = Graph()
        assert graph.root is None

    def test_add_node(self):
        """Test add node"""
        graph = Graph()
        node = Node(id="1")
        graph.add_node(node)
        assert graph.get_node("1") is not None

    def test_remove_node(self):
        """Test remove node"""
        graph = Graph()
        node = Node(id="1")
        graph.add_node(node)
        assert graph.remove_node("1") is True
        assert graph.get_node("1") is None


class TestTreeTraversalDFS:
    """Test DFS traversal"""

    @pytest.fixture
    def tree(self):
        """Create tree"""
        #       root
        #      / | \
        #     a  b  c
        #    / \    /
        #   d   e  f
        root = Node(id="root", value="root")
        a = Node(id="a", value="a")
        b = Node(id="b", value="b")
        c = Node(id="c", value="c")
        d = Node(id="d", value="d")
        e = Node(id="e", value="e")
        f = Node(id="f", value="f")

        root.add_child(a)
        root.add_child(b)
        root.add_child(c)
        a.add_child(d)
        a.add_child(e)
        c.add_child(f)

        return root

    def test_dfs(self, tree):
        """Test DFS"""
        result = TreeTraversal.dfs(tree)
        ids = [n.id for n in result]
        assert "root" in ids
        assert "a" in ids

    def test_dfs_iterative(self, tree):
        """Test iterative DFS"""
        result = TreeTraversal.dfs_iterative(tree)
        assert len(result) == 7

    def test_bfs(self, tree):
        """Test BFS"""
        result = TreeTraversal.bfs(tree)
        ids = [n.id for n in result]
        assert ids[0] == "root"
        assert len(result) == 7


class TestTreeTraversalPath:
    """Test path finding"""

    @pytest.fixture
    def tree(self):
        """Create tree"""
        root = Node(id="root")
        a = Node(id="a")
        b = Node(id="b")
        c = Node(id="c")

        root.add_child(a)
        a.add_child(b)
        b.add_child(c)

        return root

    def test_dfs_path(self, tree):
        """Test DFS path"""
        path = TreeTraversal.dfs_path(tree, "c")
        assert path is not None
        ids = [n.id for n in path]
        assert ids == ["root", "a", "b", "c"]

    def test_bfs_path(self, tree):
        """Test BFS path"""
        path = TreeTraversal.bfs_path(tree, "c")
        assert path is not None
        ids = [n.id for n in path]
        assert ids == ["root", "a", "b", "c"]

    def test_path_not_found(self, tree):
        """Test path not found"""
        path = TreeTraversal.dfs_path(tree, "missing")
        assert path is None


class TestTreeTraversalFind:
    """Test find operations"""

    @pytest.fixture
    def tree(self):
        """Create tree"""
        root = Node(id="root", value=1)
        a = Node(id="a", value=2)
        b = Node(id="b", value=3)
        root.add_child(a)
        root.add_child(b)
        return root

    def test_find_all(self, tree):
        """Test find all"""
        result = TreeTraversal.find_all(tree, lambda n: n.value > 1)
        assert len(result) == 2

    def test_find_first(self, tree):
        """Test find first"""
        result = TreeTraversal.find_first(tree, lambda n: n.value > 1)
        assert result is not None
        assert result.value == 2


class TestTreeTraversalStats:
    """Test statistics"""

    @pytest.fixture
    def tree(self):
        """Create tree"""
        root = Node(id="root")
        a = Node(id="a")
        b = Node(id="b")
        c = Node(id="c")

        root.add_child(a)
        root.add_child(b)
        b.add_child(c)

        return root

    def test_depth(self, tree):
        """Test depth"""
        depth = TreeTraversal.depth(tree)
        assert depth == 2

    def test_count_nodes(self, tree):
        """Test count nodes"""
        count = TreeTraversal.count_nodes(tree)
        assert count == 4

    def test_count_leaves(self, tree):
        """Test count leaves"""
        count = TreeTraversal.count_leaves(tree)
        assert count == 2


class TestTreeTraversalLevels:
    """Test level operations"""

    @pytest.fixture
    def tree(self):
        """Create tree"""
        #   root
        #  /   \
        # a     b
        #       \
        #        c
        root = Node(id="root")
        a = Node(id="a")
        b = Node(id="b")
        c = Node(id="c")

        root.add_child(a)
        root.add_child(b)
        b.add_child(c)

        return root

    def test_get_level(self, tree):
        """Test get level"""
        level0 = TreeTraversal.get_level(tree, 0)
        assert len(level0) == 1
        assert level0[0].id == "root"

        level1 = TreeTraversal.get_level(tree, 1)
        assert len(level1) == 2

    def test_levels(self, tree):
        """Test levels"""
        levels = TreeTraversal.levels(tree)
        assert len(levels) == 3


class TestGenerators:
    """Test generators"""

    @pytest.fixture
    def tree(self):
        """Create tree"""
        root = Node(id="root")
        a = Node(id="a")
        b = Node(id="b")
        root.add_child(a)
        root.add_child(b)
        return root

    def test_dfs_generator(self, tree):
        """Test DFS generator"""
        result = list(TreeTraversal.dfs_generator(tree))
        assert len(result) == 3

    def test_bfs_generator(self, tree):
        """Test BFS generator"""
        result = list(TreeTraversal.bfs_generator(tree))
        assert len(result) == 3


class TestHelpers:
    """Test helper functions"""

    def test_create_node(self):
        """Test create_node"""
        node = create_node("test", "value")
        assert node.id == "test"
        assert node.value == "value"
