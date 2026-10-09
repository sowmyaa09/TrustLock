"""TrustLock Controlled Telemetry Dataset Pipeline Generator.

Executes controlled M2M agent scenarios, extracts telemetry events, assigns ground-truth labels,
and exports raw JSONL traces, processed CSV dataset, and metadata.
"""
import os
import json
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any

from src.scenarios.runner import ScenarioRunner
from src.telemetry.schema import TelemetryEvent


class DatasetGenerator:
    """Generator for controlled TrustLock telemetry dataset."""

    SCENARIO_CONFIGS = [
        {
            "session_id": "session-scenario-a",
            "scenario_name": "Scenario A: Normal Workflow",
            "scenario_type": "NORMAL",
            "raw_dir": "dataset/raw/normal",
            "description": "Legitimate workflow with expected agent delegation and tool usage."
        },
        {
            "session_id": "session-scenario-b",
            "scenario_name": "Scenario B: Benign LLM Drift",
            "scenario_type": "BENIGN_DRIFT",
            "raw_dir": "dataset/raw/benign_drift",
            "description": "Safe workflow variation with structural drift but zero malicious intent."
        },
        {
            "session_id": "session-scenario-c",
            "scenario_name": "Scenario C: Indirect Prompt Injection & Escalation",
            "scenario_type": "SUSPICIOUS_EXPLOITATION",
            "raw_dir": "dataset/raw/suspicious_exploitation",
            "description": "Indirect prompt injection & unauthorized tool invocation attack."
        }
    ]

    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.processed_dir = os.path.join(self.base_dir, "dataset", "processed")
        self.metadata_dir = os.path.join(self.base_dir, "dataset", "metadata")

    def _ensure_directories(self):
        """Create dataset directory structure if it does not exist."""
        for cfg in self.SCENARIO_CONFIGS:
            os.makedirs(os.path.join(self.base_dir, cfg["raw_dir"]), exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)

    def generate(self) -> Dict[str, Any]:
        """Execute scenarios, collect telemetry, and export dataset artifacts."""
        self._ensure_directories()

        all_processed_events: List[Dict[str, Any]] = []
        events_per_class: Dict[str, int] = {}
        total_traces = len(self.SCENARIO_CONFIGS)
        total_events = 0

        for cfg in self.SCENARIO_CONFIGS:
            session_id = cfg["session_id"]
            scenario_type = cfg["scenario_type"]
            scenario_name = cfg["scenario_name"]

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

            # 2. Append to processed dataset list
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

        # 3. Export Combined Processed CSV
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

        # 4. Export Metadata Info JSON
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
            "scenario_descriptions": {cfg["scenario_type"]: cfg["description"] for cfg in self.SCENARIO_CONFIGS}
        }
        with open(metadata_path, "w", encoding="utf-8") as f_meta:
            json.dump(metadata_info, f_meta, indent=2)

        # Print Summary Output
        print("\n" + "=" * 75)
        print("TrustLock Dataset Generation Complete")
        print("=" * 75)
        print(f"Total traces           : {total_traces}")
        print(f"Total telemetry events : {total_events}\n")
        print("Events per Class:")
        for label, count in events_per_class.items():
            print(f"  - {label:<23}: {count} events")
        print("\nOutput Artifacts:")
        print(f"  - Raw JSONL Traces   : dataset/raw/")
        print(f"  - Processed CSV      : {csv_path}")
        print(f"  - Metadata Info      : {metadata_path}")
        print("=" * 75 + "\n")

        return metadata_info


def main():
    generator = DatasetGenerator()
    generator.generate()


if __name__ == "__main__":
    main()
