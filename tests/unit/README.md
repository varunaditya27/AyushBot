<div align="center">

# 🛠️ Unit Testing

**Granular Verification of Independent Functions**

</div>

## 📌 Overview

The `/tests/unit` directory contains fast, entirely isolated tests covering the smallest logical components of the codebase. By aggressively mocking out databases, file systems, and LLMs, this suite runs in less than three seconds, acting as the primary guardrail for developers during active refactoring.

## 🗂️ Test Categories

### `test_agent_intake.py`
Asserts that mathematical bounds defined by the XGBoost triage model stay intact.
- Provides static vital sign tuples `(SpO2: 85, Temp: 40C, HR: 150)`.
- **Asserts** that the pipeline definitively classifies this as `RiskTier.CRITICAL` without ever hitting the LLM API.

### `test_dijkstra.py`
Validates the local graph theory logic used by the `agent_referral` node.
- Constructs an abstract map of 5 villages.
- **Asserts** that simulating a flooded road correctly recalculates the absolute shortest valid route terminating at a District Hospital with an active ambulance logic flag.

### `test_dp_clipping.py`
Validates the Differential Privacy math in `/backend/fl/privacy.py`.
- Ingests mock neural network gradients.
- **Asserts** the L2-Norm bounds never exceed the configured $\epsilon$ threshold, guaranteeing mathematical privacy against model inversion attacks.

```mermaid
graph LR
    Function[Pure Function<br/>(e.g., L2-Norm Clip)]:::func
    Mock[Mock Data Array]:::mock
    Assert{Assert Output == Expected}:::assert
    
    Mock --> Function
    Function --> Assert
    
    classDef func fill:#e3f2fd,stroke:#1565c0
    classDef mock fill:#fff3e0,stroke:#e65100
    classDef assert fill:#e8f5e9,stroke:#2e7d32
```

## 🛠️ Execution

```bash
cd backend
# Execute only the fast unit tests, bypassing LLM/DB integrations
pytest tests/unit/
```
