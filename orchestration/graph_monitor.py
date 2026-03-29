"""
Graph Monitor - Monitoring and metrics for graphs
Мониторинг и метрики для графов
"""

import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class GraphMetrics:
    """Метрики графа"""
    node_count: int = 0
    edge_count: int = 0
    avg_degree: float = 0.0
    max_degree: int = 0
    density: float = 0.0
    is_connected: bool = False
    component_count: int = 0
    diameter: int | None = None


@dataclass
class NodeMetrics:
    """Метрики узла"""
    node_id: str
    degree: int = 0
    in_degree: int = 0
    out_degree: int = 0
    pagerank: float = 0.0
    betweenness: float = 0.0
    closeness: float = 0.0
    clustering_coef: float = 0.0


class GraphMonitor:
    """Мониторинг графа"""

    def __init__(self):
        self._history: deque = deque(maxlen=1000)
        self._callbacks: list[Callable] = []

    def record_snapshot(self, node_count: int, edge_count: int):
        """Запись снапшота"""
        snapshot = {
            "timestamp": time.time(),
            "node_count": node_count,
            "edge_count": edge_count,
        }
        self._history.append(snapshot)

    def get_history(self) -> list[dict]:
        """Получение истории"""
        return list(self._history)

    def get_growth_rate(self) -> float:
        """Скорость роста"""
        if len(self._history) < 2:
            return 0.0

        first = self._history[0]
        last = self._history[-1]

        time_diff = last["timestamp"] - first["timestamp"]
        if time_diff == 0:
            return 0.0

        node_growth = (last["node_count"] - first["node_count"]) / time_diff
        edge_growth = (last["edge_count"] - first["edge_count"]) / time_diff

        return (node_growth + edge_growth) / 2

    def register_callback(self, callback: Callable):
        """Регистрация callback"""
        self._callbacks.append(callback)

    def notify(self, event: str, data: dict):
        """Уведомление"""
        for callback in self._callbacks:
            try:
                callback(event, data)
            except Exception:
                pass


class GraphAnalyzer:
    """Анализатор графа"""

    @staticmethod
    def calculate_density(node_count: int, edge_count: int, directed: bool = False) -> float:
        """Расчёт плотности графа"""
        if node_count < 2:
            return 0.0

        max_edges = node_count * (node_count - 1)
        if not directed:
            max_edges //= 2

        return edge_count / max_edges if max_edges > 0 else 0.0

    @staticmethod
    def calculate_avg_degree(total_edges: int, node_count: int) -> float:
        """Средняя степень"""
        if node_count == 0:
            return 0.0
        return (2 * total_edges) / node_count

    @staticmethod
    def get_degree_distribution(adjacency: dict) -> dict:
        """Распределение степеней"""
        distribution = defaultdict(int)
        for neighbors in adjacency.values():
            degree = len(neighbors)
            distribution[degree] += 1
        return dict(distribution)

    @staticmethod
    def find_articulation_points(adjacency: dict[str, list], start: str = None) -> set[str]:
        """Поиск точек сочленения (удаление разрывает граф)"""
        if not adjacency:
            return set()

        visited = set()
        disc = {}
        low = {}
        parent = {}
        ap = set()
        timer = [0]

        def dfs(u):
            children = 0
            visited.add(u)
            disc[u] = low[u] = timer[0]
            timer[0] += 1

            for v, _ in adjacency.get(u, []):
                if v not in visited:
                    children += 1
                    parent[v] = u
                    dfs(v)
                    low[u] = min(low[u], low[v])

                    if parent.get(u) is None and children > 1:
                        ap.add(u)
                    if parent.get(u) is not None and low[v] >= disc[u]:
                        ap.add(u)
                elif v != parent.get(u):
                    low[u] = min(low[u], disc[v])

        start = start or next(iter(adjacency.keys()))
        dfs(start)

        # Handle disconnected graphs
        for node in adjacency:
            if node not in visited:
                dfs(node)

        return ap

    @staticmethod
    def find_bridges(adjacency: dict[str, list]) -> list[tuple]:
        """Поиск мостов (рёбра, удаление которых разрывает граф)"""
        if not adjacency:
            return []

        visited = set()
        disc = {}
        low = {}
        parent = {}
        bridges = []
        timer = [0]

        def dfs(u):
            visited.add(u)
            disc[u] = low[u] = timer[0]
            timer[0] += 1

            for v, _ in adjacency.get(u, []):
                if v not in visited:
                    parent[v] = u
                    dfs(v)
                    low[u] = min(low[u], low[v])

                    if low[v] > disc[u]:
                        bridges.append((u, v))
                elif v != parent.get(u):
                    low[u] = min(low[u], disc[v])

        start = next(iter(adjacency.keys()))
        dfs(start)

        # Handle disconnected graphs
        for node in adjacency:
            if node not in visited:
                dfs(node)

        return bridges

    @staticmethod
    def calculate_pagerank(adjacency: dict[str, list], damping: float = 0.85, iterations: int = 100) -> dict[str, float]:
        """Расчёт PageRank"""
        if not adjacency:
            return {}

        nodes = list(adjacency.keys())
        n = len(nodes)
        if n == 0:
            return {}

        # Initialize
        pr = dict.fromkeys(nodes, 1.0 / n)

        for _ in range(iterations):
            new_pr = {}
            for node in nodes:
                rank = (1 - damping) / n
                for neighbor in nodes:
                    if neighbor in adjacency:
                        neighbors = [n for n, _ in adjacency[neighbor]]
                        if node in neighbors:
                            rank += damping * pr[neighbor] / len(neighbors)
                new_pr[node] = rank
            pr = new_pr

        return pr

    @staticmethod
    def calculate_closeness_centrality(adjacency: dict[str, list], node: str) -> float:
        """Центральность по близости"""
        if node not in adjacency:
            return 0.0

        from collections import deque

        visited = {node}
        queue = deque([node])
        distances = {node: 0}

        while queue:
            current = queue.popleft()
            for neighbor, _ in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = distances[current] + 1
                    queue.append(neighbor)

        if len(distances) <= 1:
            return 0.0

        total_distance = sum(distances.values())
        n = len(visited) - 1
        return n / total_distance if total_distance > 0 else 0.0

    @staticmethod
    def calculate_betweenness_centrality(adjacency: dict[str, list], node: str) -> float:
        """Центральность по посредничеству"""
        if node not in adjacency:
            return 0.0

        nodes = list(adjacency.keys())
        n = len(nodes)
        if n <= 2:
            return 0.0

        betweenness = 0.0

        for source in nodes:
            if source == node:
                continue

            # BFS to find shortest paths
            queue = deque([source])
            predecessors = defaultdict(list)
            distances = {source: 0}

            while queue:
                current = queue.popleft()
                for neighbor, _ in adjacency.get(current, []):
                    if neighbor not in distances:
                        distances[neighbor] = distances[current] + 1
                        queue.append(neighbor)
                    if distances[neighbor] == distances[current] + 1:
                        predecessors[neighbor].append(current)

            # Count paths through node
            if node not in predecessors:
                continue

            paths = {src: 1 for src in nodes if src != source}
            for i in range(max(distances.values()), 0, -1):
                for v in nodes:
                    if distances.get(v) == i:
                        for pred in predecessors[v]:
                            paths[pred] += paths[v]

            # Accumulate betweenness
            for src in nodes:
                if src != node and src != source:
                    if node in predecessors.get(src, []):
                        betweenness += paths[src] / paths.get(source, 1)

        return betweenness / ((n - 1) * (n - 2))


class GraphVisualizer:
    """Визуализатор графа"""

    @staticmethod
    def to_dot(adjacency: dict[str, list], directed: bool = False) -> str:
        """Экспорт в DOT формат"""
        lines = ["digraph G {" if directed else "graph G {"]
        lines.append("  node [shape=circle];")

        for node, neighbors in adjacency.items():
            for neighbor, weight in neighbors:
                if directed:
                    lines.append(f'  "{node}" -> "{neighbor}" [label="{weight}"];')
                else:
                    lines.append(f'  "{node}" -- "{neighbor}" [label="{weight}"];')

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def to_adjacency_matrix(adjacency: dict[str, list]) -> dict[str, dict[str, float]]:
        """Матрица смежности"""
        nodes = list(adjacency.keys())
        matrix = {}

        for node in nodes:
            matrix[node] = dict.fromkeys(nodes, 0.0)
            for neighbor, weight in adjacency.get(node, []):
                matrix[node][neighbor] = weight

        return matrix

    @staticmethod
    def to_edge_list(adjacency: dict[str, list]) -> list[tuple]:
        """Список рёбер"""
        edges = set()
        for node, neighbors in adjacency.items():
            for neighbor, weight in neighbors:
                edge = (min(node, neighbor), max(node, neighbor), weight)
                edges.add(edge)
        return list(edges)


class GraphValidator:
    """Валидатор графа"""

    @staticmethod
    def is_valid_node(node_id: str) -> bool:
        """Валидация узла"""
        return isinstance(node_id, str) and len(node_id) > 0

    @staticmethod
    def is_valid_edge(from_node: str, to_node: str, weight: float = None) -> bool:
        """Валидация ребра"""
        if not GraphValidator.is_valid_node(from_node):
            return False
        if not GraphValidator.is_valid_node(to_node):
            return False
        if from_node == to_node:
            return False
        if weight is not None and weight < 0:
            return False
        return True

    @staticmethod
    def validate_graph(adjacency: dict[str, list]) -> tuple[bool, list[str]]:
        """Валидация всего графа"""
        errors = []

        # Check for negative weights
        for node, neighbors in adjacency.items():
            for neighbor, weight in neighbors:
                if weight < 0:
                    errors.append(f"Negative weight: {node}->{neighbor} = {weight}")

        # Check for self-loops
        for node, neighbors in adjacency.items():
            for neighbor, _ in neighbors:
                if node == neighbor:
                    errors.append(f"Self-loop: {node}")

        return len(errors) == 0, errors


# Singleton
_monitor: GraphMonitor | None = None


def get_graph_monitor() -> GraphMonitor:
    """Получение монитора графов"""
    global _monitor
    if _monitor is None:
        _monitor = GraphMonitor()
    return _monitor
