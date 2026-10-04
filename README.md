# TrustLock: Autonomous M2M Threat Detection and Revocation

> **Zero-Trust Real-Time Telemetry Framework for Detecting Anomalous Machine-to-Machine (M2M) Agentic Orchestration and Fine-Grained Permission Revocation**

---

## 🎯 Review 1 Prototype Overview

TrustLock is a Zero-Trust security monitoring framework designed for multi-agent workflows. It provides real-time telemetry extraction, dual-path structural and semantic anomaly analysis, neuro-symbolic risk state evaluation, and dynamic fine-grained capability revocation.

### Core Risk States Evaluated:
1. **`NORMAL`**: Standard expected M2M interaction. Allowed to proceed.
2. **`BENIGN_DRIFT`**: LLM hallucination or prompt formatting variance. Triggers context realignment / re-prompting **without** revoking permissions.
3. **`SUSPICIOUS_EXPLOITATION`**: Indirect prompt injection, unauthorized tool call sequence, or privilege escalation. Triggers dynamic tool/capability revocation while maintaining unrelated workflow branches.

---

## 📁 Repository Structure

```text
TrustLock/
├── config/
│   └── capabilities.json       # Initial agent roles & capability policy configuration
├── src/
│   ├── telemetry/
│   │   ├── schema.py           # Standardized Pydantic telemetry JSON models
│   │   └── logger.py           # In-memory & streaming event audit logger
│   ├── simulator/
│   │   ├── tools.py            # Mock safe tools (read_database, fetch_external_api, write_report, execute_system_command)
│   │   └── agents.py           # Planner Agent, Worker Agent A, Worker Agent B
│   ├── scenarios/
│   │   ├── runner.py           # Harness for running scenarios & telemetry analysis
│   │   ├── scenario_a_normal.py # Scenario A CLI runner
│   │   ├── scenario_b_drift.py  # Scenario B CLI runner
│   │   └── scenario_c_attack.py # Scenario C CLI runner
│   ├── analyzer/               # Dual-Path Structural & Semantic Analyzers (Phase 3)
│   ├── risk_engine/            # Neuro-Symbolic Risk Evaluator (Phase 3)
│   └── enforcer/               # Capability Manager & Attenuation Enforcer (Phase 3)
├── requirements.txt            # Minimal Python dependencies
└── README.md                   # Project documentation & run guide
```

---

## 🛠️ Prerequisites & Setup

### Requirements:
- Python 3.10+

### Installation:
```bash
# Clone the repository
git clone https://github.com/sowmyaa09/TrustLock.git
cd TrustLock

# Install dependencies
pip install -r requirements.txt
```

---

## 🧪 Running Review 1 Demonstration Scenarios

Execute the three Review 1 demonstration scenarios directly via the CLI:

### 1. Scenario A — Normal Workflow
```bash
python -m src.scenarios.scenario_a_normal
```
- **Expected Result**: Classification = `NORMAL`, Action = `ALLOW`, Capability Revocation = None.

### 2. Scenario B — Benign LLM Drift
```bash
python -m src.scenarios.scenario_b_drift
```
- **Expected Result**: Classification = `BENIGN_DRIFT`, Action = `REALIGN_CONTEXT` (Simulated re-prompting), Capability Revocation = None.

### 3. Scenario C — Indirect Prompt Injection Attack
```bash
python -m src.scenarios.scenario_c_attack
```
- **Expected Result**: Classification = `SUSPICIOUS_EXPLOITATION`, Action = `REVOKE_CAPABILITY`, Capability Revocation = `['execute:system_command']` (Worker B's high-risk tool is blocked while `write_report` stays enabled).

---

## 📋 Project Roadmap

- [x] **Phase 1: Foundation Setup & Telemetry Schema** (Completed)
- [x] **Phase 2: 3-Agent Simulator & Test Scenarios** (Completed)
- [ ] **Phase 3: Dual-Path Analyzer & Neuro-Symbolic Risk Engine**
- [ ] **Phase 4: Dashboard UI & Demonstration Integration**
