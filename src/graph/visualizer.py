"""M2M Graph Visualizer.

Renders NetworkX directed interaction graphs to high-resolution PNG images
with distinct styling for Agents, Tools, and Blocked/Attenuated security events.
"""
import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx


class GraphVisualizer:
    """Renders M2M interaction graphs into PNG visualizations."""

    @staticmethod
    def render(G: nx.DiGraph, filepath: str, title: str = None) -> None:
        """Render DiGraph into a high-DPI PNG image file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
        ax.set_facecolor("#f8fafc")
        fig.patch.set_facecolor("#f8fafc")

        # 1. Position Nodes (Layout)
        # Use bipartite layout or custom layout separating Agents (left/top) and Tools (right/bottom)
        agent_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "agent"]
        tool_nodes = [n for n, d in G.nodes(data=True) if d.get("node_type") == "tool"]

        pos = {}
        # Position agents vertically on left (x=0.2)
        for idx, agent in enumerate(sorted(agent_nodes)):
            y_pos = 1.0 - (idx + 1) * (1.0 / (len(agent_nodes) + 1))
            pos[agent] = (0.2, y_pos)

        # Position tools vertically on right (x=0.8)
        for idx, tool in enumerate(sorted(tool_nodes)):
            y_pos = 1.0 - (idx + 1) * (1.0 / (len(tool_nodes) + 1))
            pos[tool] = (0.8, y_pos)

        # Fallback to spring layout if pos incomplete
        if len(pos) < G.number_of_nodes():
            pos = nx.spring_layout(G, seed=42)

        # 2. Draw Nodes
        # Agent nodes: Circle, Blue (#1e40af)
        normal_agents = [n for n in agent_nodes if not G.nodes[n].get("is_blocked", False)]
        nx.draw_networkx_nodes(
            G, pos, nodelist=normal_agents, node_color="#1e40af", node_shape="o", node_size=2400, ax=ax, alpha=0.9
        )

        # Tool nodes: Square, Teal (#0d9488)
        normal_tools = [n for n in tool_nodes if not G.nodes[n].get("is_blocked", False)]
        nx.draw_networkx_nodes(
            G, pos, nodelist=normal_tools, node_color="#0d9488", node_shape="s", node_size=2600, ax=ax, alpha=0.9
        )

        # Blocked nodes: Red (#dc2626)
        blocked_nodes = [n for n in G.nodes() if G.nodes[n].get("is_blocked", False)]
        if blocked_nodes:
            nx.draw_networkx_nodes(
                G, pos, nodelist=blocked_nodes, node_color="#dc2626", node_shape="s", node_size=2800, ax=ax, alpha=0.95
            )

        # 3. Draw Labels
        node_labels = {n: G.nodes[n].get("label", n) for n in G.nodes()}
        nx.draw_networkx_labels(
            G, pos, labels=node_labels, font_size=8, font_weight="bold", font_color="white", font_family="sans-serif", ax=ax
        )

        # 4. Draw Edges
        normal_edges = [(u, v) for u, v, d in G.edges(data=True) if not d.get("has_blocked", False)]
        blocked_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("has_blocked", False)]

        # Normal edges (Solid dark slate arrows)
        nx.draw_networkx_edges(
            G, pos, edgelist=normal_edges, edge_color="#475569", width=2.0, arrowsize=18,
            connectionstyle="arc3,rad=0.1", ax=ax, min_source_margin=25, min_target_margin=25
        )

        # Blocked edges (Dashed thick red arrows)
        if blocked_edges:
            nx.draw_networkx_edges(
                G, pos, edgelist=blocked_edges, edge_color="#dc2626", style="dashed", width=3.0, arrowsize=22,
                connectionstyle="arc3,rad=0.1", ax=ax, min_source_margin=25, min_target_margin=25
            )

        # Edge labels (weight / call count or [BLOCKED])
        edge_labels = {}
        for u, v, d in G.edges(data=True):
            if d.get("has_blocked", False):
                edge_labels[(u, v)] = "BLOCKED"
            elif d.get("weight", 1) > 1:
                edge_labels[(u, v)] = f"x{d['weight']}"

        if edge_labels:
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=edge_labels, font_size=8, font_color="#dc2626" if blocked_edges else "#334155", ax=ax
            )

        # 5. Add Legend & Title
        legend_handles = [
            mpatches.Patch(color="#1e40af", label="Agent Node"),
            mpatches.Patch(color="#0d9488", label="Tool Node"),
            mpatches.Patch(color="#dc2626", label="Blocked Node / Interaction"),
        ]
        ax.legend(handles=legend_handles, loc="upper right", frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)

        full_title = title or G.graph.get("scenario_label", "M2M Interaction Graph")
        ax.set_title(f"TrustLock Graph: {full_title}", fontsize=14, fontweight="bold", pad=15, color="#0f172a")

        ax.axis("off")
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)
