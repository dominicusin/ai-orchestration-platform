"""
Graph recursive - DFS and BFS tree traversal
Рекурсивный обход графа: поиск в глубину и ширину
"""

from collections import deque
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """Узел графа"""
    id: str
    value: Any = None
    children: list["Node"] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_child(self, node: "Node"):
        """Добавление дочернего узла"""
        self.children.append(node)

    def is_leaf(self) -> bool:
        """Является ли листом"""
        return len(self.children) == 0


class Graph:
    """Граф/дерево"""

    def __init__(self, root: Node = None):
        self.root = root
        self._nodes: dict[str, Node] = {}

    def add_node(self, node: Node):
        """Добавление узла"""
        self._nodes[node.id] = node

    def get_node(self, node_id: str) -> Node | None:
        """Получение узла по ID"""
        return self._nodes.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        """Удаление узла"""
        if node_id in self._nodes:
            del self._nodes[node_id]
            return True
        return False


class TreeTraversal:
    """Обход дерева"""

    @staticmethod
    def dfs(root: Node, visit: Callable[[Node], None] = None) -> list[Node]:
        """Поиск в глубину (Depth-First Search)"""
        if root is None:
            return []

        result = [root]

        for child in root.children:
            result.extend(TreeTraversal.dfs(child, visit))

        if visit:
            for node in result:
                visit(node)

        return result

    @staticmethod
    def dfs_iterative(root: Node) -> list[Node]:
        """Итеративный DFS"""
        if root is None:
            return []

        result = []
        stack = [root]

        while stack:
            node = stack.pop()
            result.append(node)
            stack.extend(reversed(node.children))

        return result

    @staticmethod
    def bfs(root: Node) -> list[Node]:
        """Поиск в ширину (Breadth-First Search)"""
        if root is None:
            return []

        result = []
        queue = deque([root])

        while queue:
            node = queue.popleft()
            result.append(node)
            queue.extend(node.children)

        return result

    @staticmethod
    def dfs_path(root: Node, target_id: str) -> list[Node] | None:
        """Поиск пути DFS"""
        def dfs_recursive(node: Node, path: list[Node]) -> list[Node] | None:
            if node is None:
                return None

            path = path + [node]

            if node.id == target_id:
                return path

            for child in node.children:
                result = dfs_recursive(child, path)
                if result:
                    return result

            return None

        return dfs_recursive(root, [])

    @staticmethod
    def bfs_path(root: Node, target_id: str) -> list[Node] | None:
        """Поиск пути BFS"""
        if root is None:
            return None

        queue = deque([(root, [root])])

        while queue:
            node, path = queue.popleft()

            if node.id == target_id:
                return path

            for child in node.children:
                queue.append((child, path + [child]))

        return None

    @staticmethod
    def dfs_generator(root: Node) -> Generator[Node, None, None]:
        """Генератор DFS"""
        if root is None:
            return

        stack = [root]

        while stack:
            node = stack.pop()
            yield node
            stack.extend(reversed(node.children))

    @staticmethod
    def bfs_generator(root: Node) -> Generator[Node, None, None]:
        """Генератор BFS"""
        if root is None:
            return

        queue = deque([root])

        while queue:
            node = queue.popleft()
            yield node
            queue.extend(node.children)

    @staticmethod
    def find_all(root: Node, predicate: Callable[[Node], bool]) -> list[Node]:
        """Поиск всех узлов по предикату"""
        result = []

        for node in TreeTraversal.dfs(root):
            if predicate(node):
                result.append(node)

        return result

    @staticmethod
    def find_first(root: Node, predicate: Callable[[Node], bool]) -> Node | None:
        """Поиск первого узла по предикату"""
        for node in TreeTraversal.dfs(root):
            if predicate(node):
                return node
        return None

    @staticmethod
    def depth(root: Node) -> int:
        """Вычисление глубины дерева"""
        if root is None or root.is_leaf():
            return 0

        return 1 + max(TreeTraversal.depth(child) for child in root.children)

    @staticmethod
    def count_nodes(root: Node) -> int:
        """Подсчёт узлов"""
        return len(TreeTraversal.dfs(root))

    @staticmethod
    def count_leaves(root: Node) -> int:
        """Подсчёт листьев"""
        return sum(1 for node in TreeTraversal.dfs(root) if node.is_leaf())

    @staticmethod
    def get_level(root: Node, level: int) -> list[Node]:
        """Получение узлов на заданном уровне"""
        if level < 0:
            return []

        if level == 0:
            return [root] if root else []

        nodes_at_level = [root]
        current_level = 0

        while nodes_at_level and current_level < level:
            next_level = []
            for node in nodes_at_level:
                next_level.extend(node.children)
            nodes_at_level = next_level
            current_level += 1

        return nodes_at_level

    @staticmethod
    def levels(root: Node) -> list[list[Node]]:
        """Получение всех уровней"""
        if root is None:
            return []

        levels = []
        current_level = [root]

        while current_level:
            levels.append(current_level)
            next_level = []
            for node in current_level:
                next_level.extend(node.children)
            current_level = next_level

        return levels


class TreeBuilder:
    """Строитель дерева"""

    def __init__(self):
        self._root: Node | None = None

    def with_root(self, node_id: str, value: Any = None) -> "TreeBuilder":
        """Установка корня"""
        self._root = Node(id=node_id, value=value)
        return self

    def add_child(self, parent_id: str, node_id: str, value: Any = None) -> "TreeBuilder":
        """Добавление дочернего узла"""
        # This is a simplified version - in real use you'd track nodes
        return self

    def build(self) -> Graph:
        """Построение графа"""
        return Graph(root=self._root)


def create_node(node_id: str, value: Any = None, children: list[Node] = None) -> Node:
    """Создание узла"""
    node = Node(id=node_id, value=value)
    if children:
        node.children = children
    return node
