"""Scenario B — BENIGN_DRIFT: Safe workflow variation with structural drift but zero malicious intent."""
from src.scenarios.runner import ScenarioRunner


def main():
    runner = ScenarioRunner(
        scenario_id="session-scenario-b",
        scenario_name="Scenario B: Benign LLM Drift",
        scenario_type="BENIGN_DRIFT"
    )
    result = runner.run()
    assert result["final_risk"]["state"] == "BENIGN_DRIFT", f"Expected BENIGN_DRIFT state, got {result['final_risk']['state']}"
    assert len(result["revoked_capabilities"]) == 0, "No capabilities should be revoked in Scenario B (BENIGN_DRIFT triggers realignment only)"
    print("[PASSED] Scenario B Verification PASSED: State is BENIGN_DRIFT, context realigned, zero revocation.")


if __name__ == "__main__":
    main()
