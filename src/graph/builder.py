"""M2M Dynamic Interaction Graph Builder.

Constructs NetworkX directed dynamic interaction graphs (nx.DiGraph) from TelemetryEvent streams.
Nodes represent Agents and Tools; directed edges represent agent-to-agent delegation and tool invocation.
"""
from typing import List, Dict, Any, Tuple, Optional
import networkx as nx
from src.telemetry.schema import TelemetryEvent, OperationType, OutcomeType


class M2MGraphBuilder:
    """Builder for constructing directed dynamic interaction graphs from telemetry events."""

    KNOWN_TOOLS = {"read_database", "fetch_external_api", "write_report", "execute_system_command", "exfiltrate_data"}
    KNOWN_AGENTS = {"planner_agent", "worker_agent_a", "worker_agent_b", "reprompt_engine"}

    def __init__(self):
        pass

    def is_tool(self, node_id: str) -> bool:
        """Identify if a node represents a mock tool."""
        return node_id in self.KNOWN_TOOLS or node_id.startswith("tool_") or "_" not in node_id or node_id.endswith("_api") or node_id.endswith("_command")

    def build_graph(
        self,
        events: List[TelemetryEvent],
        session_id: Optional[str] = None,
        scenario_label: Optional[str] = None
    ) -> nx.DiGraph:
        """Construct a directed graph (nx.DiGraph) from a list of TelemetryEvent objects."""
        G = nx.DiGraph()

        if session_id:
            G.graph["session_id"] = session_id
        if scenario_label:
            G.graph["scenario_label"] = scenario_label

        for event in events:
            # Determine active nodes
            agent_id = event.agent_id
            target_agent = event.metadata.get("target_agent")
            tool_id = event.tool_id

            # 1. Add / update acting Agent node
            if not G.has_node(agent_id):
                G.add_node(
                    agent_id,
                    node_id=agent_id,
                    node_type="agent",
                    label=agent_id,
                    is_blocked=False
                )

            # 2. Add / update target Agent node if delegation message
            if event.operation == OperationType.AGENT_MESSAGE and target_agent:
                if not G.has_node(target_agent):
                    G.add_node(
                        target_agent,
                        node_id=target_agent,
                        node_type="agent",
                        label=target_agent,
                        is_blocked=False
                    )

                src, dst = agent_id, target_agent
                self._add_or_update_edge(G, src, dst, event)

            # 3. Add / update Tool node if tool invocation/response
            elif tool_id:
                if not G.has_node(tool_id):
                    G.add_node(
                        tool_id,
                        node_id=tool_id,
                        node_type="tool",
                        label=tool_id,
                        is_blocked=False
                    )

                # If event was blocked, update tool node blocked attribute
                if not event.granted_capability or event.outcome == OutcomeType.BLOCKED:
                    G.nodes[tool_id]["is_blocked"] = True

                src, dst = agent_id, tool_id
                self._add_or_update_edge(G, src, dst, event)

        return G

    def _add_or_update_edge(self, G: nx.DiGraph, src: str, dst: str, event: TelemetryEvent) -> None:
        """Helper to add or accumulate edge attributes."""
        is_event_blocked = (not event.granted_capability) or (event.outcome == OutcomeType.BLOCKED)

        if G.has_edge(src, dst):
            edge_data = G.edges[src, dst]
            edge_data["weight"] += 1
            if event.operation.value not in edge_data["operations"]:
                edge_data["operations"].append(event.operation.value)
            if event.requested_capability and event.requested_capability not in edge_data["requested_capabilities"]:
                edge_data["requested_capabilities"].append(event.requested_capability)
            edge_data["granted_capabilities"].append(event.granted_capability)
            edge_data["outcomes"].append(event.outcome.value)
            if is_event_blocked:
                edge_data["has_blocked"] = True
            edge_data["timestamp_last"] = event.timestamp
        else:
            G.add_edge(
                src,
                dst,
                source=src,
                target=dst,
                weight=1,
                operations=[event.operation.value],
                requested_capabilities=[event.requested_capability] if event.requested_capability else [],
                granted_capabilities=[event.granted_capability],
                has_blocked=is_event_blocked,
                outcomes=[event.outcome.value],
                timestamp_first=event.timestamp,
                timestamp_last=event.timestamp
            )

    @staticmethod
    def get_graph_summary(G: nx.DiGraph) -> Dict[str, Any]:
        """Compute statistical summary of interaction graph."""
        agent_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "agent"]
        tool_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "tool"]

        blocked_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("has_blocked", False)]

        interaction_ops = set()
        for u, v, d in G.edges(data=True):
            for op in d.get("operations", []):
                interaction_ops.add(op)

        return {
            "session_id": G.graph.get("session_id", "unknown"),
            "scenario_label": G.graph.get("scenario_label", "unknown"),
            "node_count": G.number_of_nodes(),
            "edge_count": G.number_of_edges(),
            "agent_count": len(agent_nodes),
            "tool_count": len(tool_nodes),
            "blocked_interaction_count": len(blocked_edges),
            "blocked_edges": blocked_edges,
            "unique_interaction_types": sorted(list(interaction_ops)),
            "observed_transitions": list(G.edges())
        }
