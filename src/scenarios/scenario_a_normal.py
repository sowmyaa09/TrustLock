"""Scenario A — NORMAL: Legitimate workflow with expected agent delegation and tool usage."""
from src.scenarios.runner import ScenarioRunner


def main():
    runner = ScenarioRunner(
        scenario_id="session-scenario-a",
        scenario_name="Scenario A: Normal Workflow",
        scenario_type="NORMAL"
    )
    result = runner.run()
    assert result["final_risk"]["state"] == "NORMAL", f"Expected NORMAL state, got {result['final_risk']['state']}"
    assert len(result["revoked_capabilities"]) == 0, "No capabilities should be revoked in Scenario A"
    print("[PASSED] Scenario A Verification PASSED: State is NORMAL and all permissions remain allowed.")


if __name__ == "__main__":
    main()
