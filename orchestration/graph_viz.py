```python
"""Visualize DAG execution graph"""

import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger("orchestration.graph_viz")


@dataclass
class NodeViz:
    """Visualization node"""
    id: str
    label: str
    type: str
    level: int
    status: str


@dataclass
class EdgeViz:
    """Visualization edge"""
    from_id: str
    to_id: str


class GraphVisualizer:
    """Visualize task DAG"""
    
    def __init__(self):
        self.nodes: List[NodeViz] = []
        self.edges: List[EdgeViz] = []
    
    def add_node(self, node: NodeViz):
        self.nodes.append(node)
    
    def add_edge(self, edge: EdgeViz):
        self.edges.append(edge)
    
    def to_mermaid(self) -> str:
        """Generate Mermaid diagram"""
        lines = ["graph TD"]
        
        # Add nodes with styling
        for node in self.nodes:
            status_class = {
                "pending": "fill:#f9f,stroke:#333",
                "running": "fill:#ff9,stroke:#333", 
                "completed": "fill:#9f9,stroke:#333",
                "failed": "fill:#f99,stroke:#333",
            }.get(node.status, "")
            
            label = f"{node.label}<br/>({node.type})"
            lines.append(f'    {node.id}["{label}"]{status_class}')
        
        # Add edges
        for edge in self.edges:
            lines.append(f"    {edge.from_id} --> {edge.to_id}")
        
        return "\n".join(lines)
    
    def to_dot(self) -> str:
        """Generate Graphviz DOT"""
        lines = ["digraph task_graph {"]
        lines.append('    rankdir=TB;')
        
        for node in self.nodes:
            color = {
                "pending": "lightgray",
                "running": "yellow",
                "completed": "lightgreen",
                "failed": "lightcoral",
            }.get(node.status, "white")
            
            lines.append(f'    {node.id} [label="{node.label}\\n({node.type})" fillcolor={color} style=filled];')
        
        for edge in self.edges:
            lines.append(f"    {edge.from_id} -> {edge.to_id};")
        
        lines.append("}")
        return "\n".join(lines)
    
    def to_json(self) -> Dict:
        """Export as JSON"""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "type": n.type,
                    "level": n.level,
                    "status": n.status,
                }
                for n in self.nodes
            ],
            "edges": [
                {"from": e.from_id, "to": e.to_id}
                for e in self.edges
            ],
        }
    
    def to_ascii(self) -> str:
        """Generate ASCII art"""
        lines = ["Task Graph:", "=" * 40]
        
        # Group by level
        by_level = {}
        for node in self.nodes:
            if node.level not in by_level:
                by_level[node.level] = []
            by_level[node.level].append(node)
        
        for level in sorted(by_level.keys()):
            nodes = by_level[level]
            level_str = f"Level {level}: " + ", ".join(n.label for n in nodes)
            lines.append(level_str)
        
        return "\n".join(lines)


class ExecutionTimeline:
    """Timeline of task execution"""
    
    def __init__(self):
        self.events: List[Dict] = []
    
    def add_event(self, task_id: str, event_type: str, timestamp: float = None):
        import time
        self.events.append({
            "task_id": task_id,
            "event": event_type,
            "timestamp": timestamp or time.time(),
        })
    
    def get_timeline(self) -> List[Dict]:
        return sorted(self.events, key=lambda x: x["timestamp"])
    
    def to_gantt(self) -> str:
        """Generate Gantt chart (Mermaid)"""
        lines = ["gantt"]
        lines.append("    title Task Execution Timeline")
        lines.append("    dateFormat X")
        lines.append("    axisFormat %s")
        
        # This would need start/end times
        return "\n".join(lines)


def visualize_task_graph(graph) -> GraphVisualizer:
    """Create visualizer from task graph"""
    # Import at runtime to avoid circular import
    from orchestration.graph_integration import TaskGraph
    
    viz = GraphVisualizer()
    
    for task_id, task in graph.tasks.items():
        viz.add_node(NodeViz(
            id=task_id,
            label=task.name,
            type=task.task_type.value,
            level=task.level,
            status=task.status,
        ))
    
    for from_id, to_ids in graph.edges.items():
        for to_id in to_ids:
            viz.add_edge(EdgeViz(from_id, to_id))
    
    return viz
```