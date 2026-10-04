"""Scenario C — SUSPICIOUS_EXPLOITATION: Indirect prompt injection & unauthorized tool invocation attack."""
from src.scenarios.runner import ScenarioRunner


def main():
    runner = ScenarioRunner(
        scenario_id="session-scenario-c",
        scenario_name="Scenario C: Indirect Prompt Injection & Escalation",
        scenario_type="SUSPICIOUS_EXPLOITATION"
    )
    result = runner.run()
    assert result["final_risk"]["state"] == "SUSPICIOUS_EXPLOITATION", f"Expected SUSPICIOUS_EXPLOITATION state, got {result['final_risk']['state']}"
    assert "execute:system_command" in result["revoked_capabilities"], "Capability 'execute:system_command' must be revoked in Scenario C"
    print("[PASSED] Scenario C Verification PASSED: State is SUSPICIOUS_EXPLOITATION and 'execute:system_command' was revoked.")


if __name__ == "__main__":
    main()
