"""Test and validation script for TrustLock Dynamic M2M Interaction Graph Pipeline."""
import os
import json
from src.scenarios.runner import ScenarioRunner
from src.analyzer.structural import StructuralAnalyzer
from src.graph.builder import M2MGraphBuilder
from src.graph.exporter import GraphExporter
from src.graph.visualizer import GraphVisualizer


def run_graph_validation():
    """Build, export, visualize, and validate interaction graphs for all scenarios."""
    out_dir = "dataset/graphs"
    os.makedirs(out_dir, exist_ok=True)

    scenarios = [
        {"id": "session-scenario-a", "name": "Scenario A: Normal Workflow", "label": "NORMAL", "file_prefix": "normal_graph"},
        {"id": "session-scenario-b", "name": "Scenario B: Benign LLM Drift", "label": "BENIGN_DRIFT", "file_prefix": "benign_drift_graph"},
        {"id": "session-scenario-c", "name": "Scenario C: Indirect Prompt Injection & Escalation", "label": "SUSPICIOUS_EXPLOITATION", "file_prefix": "suspicious_exploitation_graph"}
    ]

    builder = M2MGraphBuilder()
    struct_analyzer = StructuralAnalyzer()

    print("\n" + "=" * 75)
    print("TrustLock M2M Interaction Graph Pipeline Validation")
    print("=" * 75 + "\n")

    for sc in scenarios:
        session_id = sc["id"]
        label = sc["label"]
        prefix = sc["file_prefix"]

        # 1. Run scenario to collect telemetry events
        runner = ScenarioRunner(scenario_id=session_id, scenario_name=sc["name"], scenario_type=label)
        runner.run()
        events = runner.logger.get_events(session_id)

        # 2. Build nx.DiGraph
        G = builder.build_graph(events, session_id=session_id, scenario_label=label)
        summary = builder.get_graph_summary(G)

        # 3. Export JSON, GraphML, GIN data, and render PNG
        json_path = os.path.join(out_dir, f"{prefix}.json")
        graphml_path = os.path.join(out_dir, f"{prefix}.graphml")
        png_path = os.path.join(out_dir, f"{prefix}.png")
        gin_json_path = os.path.join(out_dir, f"{prefix}_gin.json")

        GraphExporter.export_json(G, json_path)
        GraphExporter.export_graphml(G, graphml_path)
        GraphVisualizer.render(G, png_path, title=f"{sc['name']} [{label}]")

        gin_data = GraphExporter.to_gin_data(G, scenario_label=label)
        with open(gin_json_path, "w", encoding="utf-8") as f:
            json.dump(gin_data, f, indent=2)

        # 4. Compare with StructuralAnalyzer
        struct_res = struct_analyzer.analyze(events)

        print(f"\n--- GRAPH SUMMARY: {sc['name']} [{label}] ---")
        print(f"Nodes ({summary['node_count']})                  : {list(G.nodes())}")
        print(f"Edges ({summary['edge_count']})                  : {summary['observed_transitions']}")
        print(f"Agent Count              : {summary['agent_count']}")
        print(f"Tool Count               : {summary['tool_count']}")
        print(f"Blocked Interactions     : {summary['blocked_interaction_count']} {summary['blocked_edges']}")
        print(f"GIN Node Matrix Shape    : {len(gin_data['x'])}x{len(gin_data['x'][0])} (y={gin_data['y']})")
        print(f"StructuralAnalyzer Check : Score={struct_res.structural_score:.2f}, Edge Count={struct_res.graph_metrics['edge_count']}")

        # 5. Assertions / Validations
        if label == "NORMAL":
            assert summary["edge_count"] == 5, f"Normal graph expected 5 edges, got {summary['edge_count']}"
            assert summary["blocked_interaction_count"] == 0, "Normal graph should have 0 blocked interactions"
        elif label == "BENIGN_DRIFT":
            assert ("worker_agent_a", "fetch_external_api") in summary["observed_transitions"], "Benign drift missing API interaction"
            assert G.edges[("worker_agent_a", "fetch_external_api")]["weight"] >= 4, "Benign drift API edge weight should be at least 4"
            assert summary["blocked_interaction_count"] == 0, "Benign drift graph should have 0 blocked interactions"
        elif label == "SUSPICIOUS_EXPLOITATION":
            assert ("worker_agent_b", "execute_system_command") in summary["observed_transitions"], "Suspicious exploitation missing execute_system_command transition"
            assert G.edges[("worker_agent_b", "execute_system_command")]["has_blocked"] is True, "execute_system_command edge must be marked blocked"
            assert summary["blocked_interaction_count"] >= 1, "Suspicious exploitation must contain blocked interactions"

        # Assert consistency with StructuralAnalyzer node/edge counts
        assert summary["node_count"] == struct_res.graph_metrics["node_count"], "Node count mismatch between GraphBuilder and StructuralAnalyzer"

        print(f"[PASSED] Validation Passed for {label}!")

    print("\n" + "=" * 75)
    print("[SUCCESS] ALL GRAPH PIPELINE VALIDATION CHECKS PASSED SUCCESSFULLY!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_graph_validation()
