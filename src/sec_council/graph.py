"""Small provenance and decision graph, without a heavy graph database."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Node:
    node_id: str
    kind: str
    label: str
    source: str = ""
    status: str = "UNVERIFIED"


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    relationship: str


@dataclass
class EvidenceGraph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> None:
        if node.node_id in self.nodes and self.nodes[node.node_id] != node:
            raise ValueError("Conflicting node identity")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.src not in self.nodes or edge.dst not in self.nodes:
            raise ValueError("Edges must reference existing nodes")
        if edge.relationship not in {
            "DEPENDS_ON", "SUPPORTED_BY", "CONTRADICTS", "IMPLEMENTS", "SUPERSEDES", "CITES",
        }:
            raise ValueError("Unsupported relationship")
        if edge not in self.edges:
            self.edges.append(edge)

    def to_dict(self) -> dict:
        return {"nodes": [asdict(n) for n in self.nodes.values()],
                "edges": [asdict(e) for e in self.edges]}
