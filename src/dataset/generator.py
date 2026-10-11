"""TrustLock Controlled Telemetry Dataset Pipeline Generator.

Executes controlled M2M agent scenarios, extracts telemetry events, assigns ground-truth labels,
constructs M2M interaction graphs, and exports raw JSONL traces, processed CSV dataset,
metadata, and visual graph artifacts.
"""
import os
import json
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.scenarios.runner import ScenarioRunner
from src.telemetry.schema import TelemetryEvent
from src.graph.builder import M2MGraphBuilder
from src.graph.exporter import GraphExporter
from src.graph.visualizer import GraphVisualizer


class DatasetGenerator:
    """Generator for controlled TrustLock telemetry dataset and graph artifacts."""

    SCENARIO_CONFIGS = [
        {
            "session_id": "session-scenario-a",
            "scenario_name": "Scenario A: Normal Workflow",
            "scenario_type": "NORMAL",
            "raw_dir": "dataset/raw/normal",
            "graph_prefix": "normal_graph",
            "description": "Legitimate workflow with expected agent delegation and tool usage."
        },
        {
            "session_id": "session-scenario-b",
            "scenario_name": "Scenario B: Benign LLM Drift",
            "scenario_type": "BENIGN_DRIFT",
            "raw_dir": "dataset/raw/benign_drift",
            "graph_prefix": "benign_drift_graph",
            "description": "Safe workflow variation with structural drift but zero malicious intent."
        },
        {
            "session_id": "session-scenario-c",
            "scenario_name": "Scenario C: Indirect Prompt Injection & Escalation",
            "scenario_type": "SUSPICIOUS_EXPLOITATION",
            "raw_dir": "dataset/raw/suspicious_exploitation",
            "graph_prefix": "suspicious_exploitation_graph",
            "description": "Indirect prompt injection & unauthorized tool invocation attack."
        }
    ]

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.processed_dir = os.path.join(self.base_dir, "dataset", "processed")
        self.metadata_dir = os.path.join(self.base_dir, "dataset", "metadata")
        self.graphs_dir = os.path.join(self.base_dir, "dataset", "graphs")
        self.graph_builder = M2MGraphBuilder()

    def _ensure_directories(self):
        """Create dataset directory structure if it does not exist."""
        for cfg in self.SCENARIO_CONFIGS:
            os.makedirs(os.path.join(self.base_dir, cfg["raw_dir"]), exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.graphs_dir, exist_ok=True)

    def generate(self) -> Dict[str, Any]:
        """Execute scenarios, collect telemetry, build interaction graphs, and export dataset artifacts."""
        self._ensure_directories()

        all_processed_events: List[Dict[str, Any]] = []
        events_per_class: Dict[str, int] = {}
        graph_summaries: Dict[str, Any] = {}
        total_traces = len(self.SCENARIO_CONFIGS)
        total_events = 0

        for cfg in self.SCENARIO_CONFIGS:
            session_id = cfg["session_id"]
            scenario_type = cfg["scenario_type"]
            scenario_name = cfg["scenario_name"]
            prefix = cfg["graph_prefix"]

            # Execute scenario via existing runner
            runner = ScenarioRunner(
                scenario_id=session_id,
                scenario_name=scenario_name,
                scenario_type=scenario_type
            )
            runner.run()

            events: List[TelemetryEvent] = runner.logger.get_events(session_id)
            events_per_class[scenario_type] = len(events)
            total_events += len(events)

            # 1. Export Raw JSONL for this scenario
            raw_path = os.path.join(self.base_dir, cfg["raw_dir"], f"{session_id}.jsonl")
            with open(raw_path, "w", encoding="utf-8") as f_raw:
                for event in events:
                    event_dict = event.model_dump()
                    event_dict["ground_truth_label"] = scenario_type
                    event_dict["scenario_name"] = scenario_name
                    f_raw.write(json.dumps(event_dict) + "\n")

            # 2. Build & Export Dynamic Interaction Graph Artifacts
            G = self.graph_builder.build_graph(events, session_id=session_id, scenario_label=scenario_type)
            summary = self.graph_builder.get_graph_summary(G)
            graph_summaries[scenario_type] = summary

            json_path = os.path.join(self.graphs_dir, f"{prefix}.json")
            graphml_path = os.path.join(self.graphs_dir, f"{prefix}.graphml")
            png_path = os.path.join(self.graphs_dir, f"{prefix}.png")
            gin_json_path = os.path.join(self.graphs_dir, f"{prefix}_gin.json")

            GraphExporter.export_json(G, json_path)
            GraphExporter.export_graphml(G, graphml_path)
            GraphVisualizer.render(G, png_path, title=f"{scenario_name} [{scenario_type}]")

            gin_data = GraphExporter.to_gin_data(G, scenario_label=scenario_type)
            with open(gin_json_path, "w", encoding="utf-8") as f:
                json.dump(gin_data, f, indent=2)

            # 3. Append to processed dataset list
            for idx, event in enumerate(events, 1):
                processed_row = {
                    "event_id": f"{session_id}-{idx:03d}",
                    "timestamp": event.timestamp,
                    "session_id": event.session_id,
                    "agent_id": event.agent_id,
                    "parent_agent": event.parent_agent or "",
                    "tool_id": event.tool_id or "",
                    "operation": event.operation.value,
                    "requested_capability": event.requested_capability or "",
                    "granted_capability": event.granted_capability,
                    "outcome": event.outcome.value,
                    "text_context": event.text_context,
                    "scenario": scenario_name,
                    "ground_truth_label": scenario_type
                }
                all_processed_events.append(processed_row)

        # 4. Export Combined Processed CSV
        csv_path = os.path.join(self.processed_dir, "trustlock_dataset.csv")
        fieldnames = [
            "event_id", "timestamp", "session_id", "agent_id", "parent_agent",
            "tool_id", "operation", "requested_capability", "granted_capability",
            "outcome", "text_context", "scenario", "ground_truth_label"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_processed_events)

        # 5. Export Metadata Info JSON
        metadata_path = os.path.join(self.metadata_dir, "dataset_info.json")
        metadata_info = {
            "dataset_name": "TrustLock Controlled Telemetry Dataset",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "controlled local simulator",
            "note": "Controlled ground-truth security telemetry traces collected from the TrustLock 3-agent M2M simulation.",
            "total_traces": total_traces,
            "total_events": total_events,
            "class_labels": ["NORMAL", "BENIGN_DRIFT", "SUSPICIOUS_EXPLOITATION"],
            "events_per_class": events_per_class,
            "graph_summaries": graph_summaries,
            "scenario_descriptions": {cfg["scenario_type"]: cfg["description"] for cfg in self.SCENARIO_CONFIGS}
        }
        with open(metadata_path, "w", encoding="utf-8") as f_meta:
            json.dump(metadata_info, f_meta, indent=2)

        # Print Summary Output
        print("\n" + "=" * 75)
        print("TrustLock Dataset & Graph Generation Complete")
        print("=" * 75)
        print(f"Total traces           : {total_traces}")
        print(f"Total telemetry events : {total_events}\n")
        print("Events per Class:")
        for label, count in events_per_class.items():
            print(f"  - {label:<23}: {count} events")

        print("\nGraph Summaries:")
        for label, s in graph_summaries.items():
            print(f"  - {label:<23}: {s['node_count']} nodes ({s['agent_count']} agents, {s['tool_count']} tools), {s['edge_count']} edges, {s['blocked_interaction_count']} blocked")

        print("\nOutput Artifacts:")
        print(f"  - Raw JSONL Traces   : dataset/raw/")
        print(f"  - Processed CSV      : {csv_path}")
        print(f"  - Metadata Info      : {metadata_path}")
        print(f"  - Graph Exports      : dataset/graphs/ (JSON, GraphML, GIN, PNG)")
        print("=" * 75 + "\n")

        return metadata_info


def main():
    generator = DatasetGenerator()
    generator.generate()


if __name__ == "__main__":
    main()
