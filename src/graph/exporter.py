"""M2M Graph Exporter & GIN Feature Extractor.

Provides utilities for exporting NetworkX interaction graphs to machine-readable formats
(Node-Link JSON, GraphML) and generating GIN (Graph Isomorphism Network) dataset format.
"""
import os
import json
from typing import Dict, Any
import networkx as nx


class GraphExporter:
    """Exporter for graph visualization artifacts and GIN feature matrices."""

    @staticmethod
    def export_json(G: nx.DiGraph, filepath: str) -> None:
        """Export graph to standard Node-Link JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data = nx.node_link_data(G)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def export_graphml(G: nx.DiGraph, filepath: str) -> None:
        """Export graph to GraphML format for Gephi/NetworkX analysis."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        # Create sanitized copy with primitive attributes suitable for GraphML
        G_clean = nx.DiGraph()
        G_clean.graph.update({k: str(v) for k, v in G.graph.items()})

        for n, d in G.nodes(data=True):
            clean_attr = {}
            for k, v in d.items():
                if isinstance(v, (list, dict)):
                    clean_attr[k] = json.dumps(v)
                else:
                    clean_attr[k] = v
            G_clean.add_node(n, **clean_attr)

        for u, v, d in G.edges(data=True):
            clean_attr = {}
            for k, val in d.items():
                if isinstance(val, (list, dict)):
                    clean_attr[k] = json.dumps(val)
                else:
                    clean_attr[k] = val
            G_clean.add_edge(u, v, **clean_attr)

        nx.write_graphml(G_clean, filepath)

    @staticmethod
    def to_gin_data(G: nx.DiGraph, scenario_label: str = "NORMAL") -> Dict[str, Any]:
        """Convert NetworkX DiGraph into PyTorch Geometric / GIN compatible representation.

        Outputs:
        - node_mapping: Dict[node_name -> int_index]
        - x: List of node feature vectors [is_agent, is_tool, is_blocked]
        - edge_index: [2, E] edge pairs [[src_indices], [dst_indices]]
        - edge_attr: List of edge feature vectors [weight, has_blocked]
        - y: Target class label index (0: NORMAL, 1: BENIGN_DRIFT, 2: SUSPICIOUS_EXPLOITATION)
        """
        label_map = {
            "NORMAL": 0,
            "BENIGN_DRIFT": 1,
            "SUSPICIOUS_EXPLOITATION": 2
        }

        nodes = sorted(list(G.nodes()))
        node_mapping = {n: idx for idx, n in enumerate(nodes)}

        # Node feature matrix: x = [is_agent (1/0), is_tool (1/0), is_blocked (1/0)]
        x = []
        for n in nodes:
            attr = G.nodes[n]
            is_agent = 1.0 if attr.get("node_type") == "agent" else 0.0
            is_tool = 1.0 if attr.get("node_type") == "tool" else 0.0
            is_blocked = 1.0 if attr.get("is_blocked", False) else 0.0
            x.append([is_agent, is_tool, is_blocked])

        # Edge index tensor representation [[src...], [dst...]] & Edge features [weight, has_blocked]
        src_list = []
        dst_list = []
        edge_attr = []

        for u, v, attr in G.edges(data=True):
            src_idx = node_mapping[u]
            dst_idx = node_mapping[v]
            src_list.append(src_idx)
            dst_list.append(dst_idx)

            weight = float(attr.get("weight", 1))
            has_blocked = 1.0 if attr.get("has_blocked", False) else 0.0
            edge_attr.append([weight, has_blocked])

        edge_index = [src_list, dst_list]
        y_class = label_map.get(scenario_label, 0)

        return {
            "scenario_label": scenario_label,
            "y": y_class,
            "node_mapping": node_mapping,
            "x": x,
            "edge_index": edge_index,
            "edge_attr": edge_attr,
            "num_nodes": len(nodes),
            "num_edges": len(src_list)
        }
