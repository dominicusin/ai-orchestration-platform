"""
Graph Engine - Graph operations and algorithms
Движок графов - операции и алгоритмы на графах
"""

import heapq
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Edge:
    """Ребро графа"""
    from_node: str
    to_node: str
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class GraphNode:
    """Узел графа"""
    id: str
    value: Any = None
    metadata: dict = field(default_factory=dict)


class GraphEngine:
    """Движок графов с алгоритмами"""

    def __init__(self, directed: bool = False):
        self.directed = directed
        self._nodes: dict[str, GraphNode] = {}
        self._adjacency: dict[str, list[tuple[str, float]]] = defaultdict(list)
        self._edges: list[Edge] = []

    def add_node(self, node_id: str, value: Any = None, metadata: dict = None) -> "GraphEngine":
        """Добавление узла"""
        self._nodes[node_id] = GraphNode(id=node_id, value=value, metadata=metadata or {})
        if node_id not in self._adjacency:
            self._adjacency[node_id] = []
        return self

    def add_edge(self, from_node: str, to_node: str, weight: float = 1.0, metadata: dict = None) -> "GraphEngine":
        """Добавление ребра"""
        # Ensure nodes exist
        if from_node not in self._nodes:
            self.add_node(from_node)
        if to_node not in self._nodes:
            self.add_node(to_node)

        self._adjacency[from_node].append((to_node, weight))
        if not self.directed:
            self._adjacency[to_node].append((from_node, weight))

        edge = Edge(from_node, to_node, weight, metadata or {})
        self._edges.append(edge)
        return self

    def get_node(self, node_id: str) -> GraphNode | None:
        """Получение узла"""
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> list[str]:
        """Получение соседей узла"""
        return [neighbor for neighbor, _ in self._adjacency.get(node_id, [])]

    def get_edges(self) -> list[Edge]:
        """Получение всех рёбер"""
        return self._edges

    def node_count(self) -> int:
        """Количество узлов"""
        return len(self._nodes)

    def edge_count(self) -> int:
        """Количество рёбер"""
        return len(self._edges)

    def has_node(self, node_id: str) -> bool:
        """Проверка существования узла"""
        return node_id in self._nodes

    def has_edge(self, from_node: str, to_node: str) -> bool:
        """Проверка существования ребра"""
        neighbors = self.get_neighbors(from_node)
        return to_node in neighbors

    def remove_node(self, node_id: str) -> bool:
        """Удаление узла"""
        if node_id not in self._nodes:
            return False

        del self._nodes[node_id]
        del self._adjacency[node_id]

        # Remove edges
        self._edges = [e for e in self._edges if e.from_node != node_id and e.to_node != node_id]
        self._adjacency = {
            k: [(n, w) for n, w in v if n != node_id]
            for k, v in self._adjacency.items()
        }
        return True

    def remove_edge(self, from_node: str, to_node: str) -> bool:
        """Удаление ребра"""
        original_count = len(self._edges)
        self._edges = [
            e for e in self._edges
            if not (e.from_node == from_node and e.to_node == to_node)
        ]
        return len(self._edges) < original_count

    def dijkstra(self, start: str, end: str) -> tuple[list[str], float] | None:
        """Алгоритм Дейкстры"""
        if start not in self._nodes or end not in self._nodes:
            return None

        distances = {node: float('inf') for node in self._nodes}
        distances[start] = 0
        previous = dict.fromkeys(self._nodes)
        pq = [(0, start)]

        while pq:
            current_dist, current = heapq.heappop(pq)

            if current == end:
                break

            if current_dist > distances[current]:
                continue

            for neighbor, weight in self._adjacency[current]:
                distance = current_dist + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))

        if distances[end] == float('inf'):
            return None

        # Reconstruct path
        path = []
        current = end
        while current:
            path.append(current)
            current = previous[current]
        path.reverse()

        return path, distances[end]

    def bfs(self, start: str) -> list[str]:
        """Поиск в ширину"""
        if start not in self._nodes:
            return []

        visited = {start}
        queue = deque([start])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor, _ in self._adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return result

    def dfs(self, start: str) -> list[str]:
        """Поиск в глубину"""
        if start not in self._nodes:
            return []

        visited = set()
        result = []
        stack = [start]

        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                result.append(node)

                # Add neighbors in reverse order for consistent ordering
                neighbors = [n for n, _ in self._adjacency[node]]
                stack.extend(reversed(neighbors))

        return result

    def topological_sort(self) -> list[str] | None:
        """Топологическая сортировка"""
        if not self.directed:
            return None

        in_degree = dict.fromkeys(self._nodes, 0)
        for edge in self._edges:
            in_degree[edge.to_node] += 1

        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)

            for neighbor, _ in self._adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._nodes):
            return None  # Cycle detected

        return result

    def find_path(self, start: str, end: str) -> list[str] | None:
        """Поиск пути (BFS)"""
        if start not in self._nodes or end not in self._nodes:
            return None

        visited = {start}
        queue = deque([(start, [start])])

        while queue:
            node, path = queue.popleft()

            if node == end:
                return path

            for neighbor, _ in self._adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    def find_all_paths(self, start: str, end: str) -> list[list[str]]:
        """Поиск всех путей"""
        if start not in self._nodes or end not in self._nodes:
            return []

        paths = []

        def dfs(current: str, path: list[str]):
            if current == end:
                paths.append(path)
                return

            for neighbor, _ in self._adjacency[current]:
                if neighbor not in path:
                    dfs(neighbor, path + [neighbor])

        dfs(start, [start])
        return paths

    def is_connected(self) -> bool:
        """Проверка связности графа"""
        if not self._nodes:
            return True

        visited = set(self.bfs(list(self._nodes.keys())[0]))
        return len(visited) == len(self._nodes)

    def get_connected_components(self) -> list[set[str]]:
        """Получение компонент связности"""
        visited = set()
        components = []

        for node in self._nodes:
            if node not in visited:
                component = set(self.bfs(node))
                visited.update(component)
                components.append(component)

        return components

    def degree(self, node_id: str) -> int:
        """Степень узла"""
        if node_id not in self._nodes:
            return 0
        return len(self._adjacency[node_id])

    def clear(self):
        """Очистка графа"""
        self._nodes.clear()
        self._adjacency.clear()
        self._edges.clear()


class WeightedGraphEngine(GraphEngine):
    """Взвешенный граф"""

    def __init__(self, directed: bool = False):
        super().__init__(directed)

    def get_weight(self, from_node: str, to_node: str) -> float | None:
        """Получение веса ребра"""
        for neighbor, weight in self._adjacency.get(from_node, []):
            if neighbor == to_node:
                return weight
        return None

    def prim_mst(self) -> Optional["GraphEngine"]:
        """Алгоритм Прима для минимального остовного дерева"""
        if not self._nodes:
            return None

        mst = WeightedGraphEngine(self.directed)

        start_node = next(iter(self._nodes))
        visited = {start_node}
        mst.add_node(start_node)

        while len(visited) < len(self._nodes):
            min_edge = None
            min_weight = float('inf')

            for node in visited:
                for neighbor, weight in self._adjacency[node]:
                    if neighbor not in visited and weight < min_weight:
                        min_weight = weight
                        min_edge = (node, neighbor)

            if not min_edge:
                break

            from_node, to_node = min_edge
            visited.add(to_node)
            mst.add_node(to_node)
            mst.add_edge(from_node, to_node, min_weight)

        return mst

    def bellman_ford(self, start: str) -> dict[str, float] | None:
        """Алгоритм Беллмана-Форда"""
        if start not in self._nodes:
            return None

        distances = {node: float('inf') for node in self._nodes}
        distances[start] = 0

        # Relax edges |V| - 1 times
        for _ in range(len(self._nodes) - 1):
            for edge in self._edges:
                if distances[edge.from_node] + edge.weight < distances[edge.to_node]:
                    distances[edge.to_node] = distances[edge.from_node] + edge.weight

        # Check for negative cycles
        for edge in self._edges:
            if distances[edge.from_node] + edge.weight < distances[edge.to_node]:
                return None  # Negative cycle detected

        return distances


def create_graph(directed: bool = False) -> GraphEngine:
    """Создание графа"""
    return GraphEngine(directed)


def create_weighted_graph(directed: bool = False) -> WeightedGraphEngine:
    """Создание взвешенного графа"""
    return WeightedGraphEngine(directed)
