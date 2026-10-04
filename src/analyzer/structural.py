"""Lightweight Structural Graph & Workflow Transition Analyzer.

Constructs dynamic interaction graphs from TelemetryEvents, evaluates transition statistics
against baseline workflow graph models, and outputs normalized structural anomaly scores.

Designed to be GIN (Graph Isomorphism Network) ready for seamless GNN upgrades.
"""
from typing import List, Dict, Any, Tuple, Set, Optional
from pydantic import BaseModel, Field
from src.telemetry.schema import TelemetryEvent, OperationType


class StructuralAnalysisResult(BaseModel):
    """Output container for structural graph analysis evidence."""

    structural_score: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized structural anomaly score [0.0 - 1.0]"
    )
    observed_edges: List[Tuple[str, str]] = Field(
        default_factory=list, description="List of directed edges (source -> target) in session graph"
    )
    observed_nodes: List[str] = Field(
        default_factory=list, description="List of unique active nodes in interaction graph"
    )
    deviations: List[str] = Field(
        default_factory=list, description="Detailed list of structural anomalies/deviations detected"
    )
    graph_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Graph metrics (edge count, node count, transition frequencies)"
    )


class StructuralAnalyzer:
    """Lightweight structural graph analyzer."""

    # Standard expected workflow edges (Baseline Graph Model)
    DEFAULT_BASELINE_EDGES: Set[Tuple[str, str]] = {
        ("planner_agent", "worker_agent_a"),
        ("worker_agent_a", "read_database"),
        ("worker_agent_a", "fetch_external_api"),
        ("planner_agent", "worker_agent_b"),
        ("worker_agent_b", "write_report"),
    }

    # Explicit high-risk prohibited transitions
    HIGH_RISK_TRANSITIONS: Set[Tuple[str, str]] = {
        ("worker_agent_a", "execute_system_command"),
        ("worker_agent_b", "execute_system_command"),
        ("worker_agent_a", "exfiltrate_data"),
        ("worker_agent_b", "exfiltrate_data"),
    }

    def __init__(self, baseline_edges: Optional[Set[Tuple[str, str]]] = None):
        self.baseline_edges = baseline_edges if baseline_edges is not None else self.DEFAULT_BASELINE_EDGES

    def extract_graph(self, events: List[TelemetryEvent]) -> Tuple[List[str], List[Tuple[str, str]], Dict[Tuple[str, str], int]]:
        """Construct graph nodes, directed edges, and edge frequencies from telemetry events."""
        nodes: Set[str] = set()
        edges: List[Tuple[str, str]] = []
        edge_counts: Dict[Tuple[str, str], int] = {}

        for event in events:
            nodes.add(event.agent_id)

            # Agent-to-Agent Delegation Edge
            if event.operation == OperationType.AGENT_MESSAGE:
                target_agent = event.metadata.get("target_agent")
                if target_agent:
                    nodes.add(target_agent)
                    edge = (event.agent_id, target_agent)
                    edges.append(edge)
                    edge_counts[edge] = edge_counts.get(edge, 0) + 1

            # Agent-to-Tool Invocation Edge
            elif event.operation == OperationType.TOOL_INVOCATION and event.tool_id:
                nodes.add(event.tool_id)
                edge = (event.agent_id, event.tool_id)
                edges.append(edge)
                edge_counts[edge] = edge_counts.get(edge, 0) + 1

        return sorted(list(nodes)), edges, edge_counts

    def analyze(self, events: List[TelemetryEvent]) -> StructuralAnalysisResult:
        """Analyze telemetry sequence graph and compute structural anomaly score."""
        nodes, edges, edge_counts = self.extract_graph(events)
        unique_edges = set(edges)
        deviations: List[str] = []

        raw_score = 0.0

        # 1. Check for High-Risk / Prohibited Transitions
        for edge in unique_edges:
            src, tgt = edge
            if edge in self.HIGH_RISK_TRANSITIONS:
                raw_score += 0.85
                deviations.append(
                    f"High-Risk Structural Transition: '{src}' -> '{tgt}' is a prohibited high-risk transition."
                )
            elif edge not in self.baseline_edges:
                raw_score += 0.40
                deviations.append(
                    f"Unexpected Edge: '{src}' -> '{tgt}' is not present in expected baseline workflow graph."
                )

        # 2. Check for Edge Frequency & Sequence Anomalies (e.g. redundant tool loops)
        for edge, count in edge_counts.items():
            src, tgt = edge
            if count > 1 and edge in self.baseline_edges:
                raw_score += 0.35
                deviations.append(
                    f"Unusual Sequence Frequency: Edge '{src}' -> '{tgt}' occurred {count} times (baseline expectation is 1)."
                )

        # Normalize score between 0.0 and 1.0
        structural_score = round(min(max(raw_score, 0.0), 1.0), 2)

        return StructuralAnalysisResult(
            structural_score=structural_score,
            observed_edges=edges,
            observed_nodes=nodes,
            deviations=deviations,
            graph_metrics={
                "node_count": len(nodes),
                "edge_count": len(edges),
                "unique_edge_count": len(unique_edges),
                "edge_frequencies": {f"{src}->{tgt}": count for (src, tgt), count in edge_counts.items()},
            }
        )
