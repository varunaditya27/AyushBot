<div align="center">

# 🧪 AyushBot Test Suite

**Ensuring Clinical Reliability Across the Software Stack**

</div>

## 📌 Overview

Because AyushBot provides direct medical triage decision support (up to life-saving IMCI interventions), its code must be rigorously verified. The `/tests` directory centralizes all unit, integration, and end-to-end (E2E) testing frameworks for the backend, cloud, and ML components. 

*\*Note: Android UI tests (Espresso/Compose Rules) live directly within the `/android/app/src/androidTest` structure.*

## ⚖️ Testing Pyramid

```mermaid
graph TD
    %% Tiers
    Unit[🛠️ Unit Tests<br/>(Pytest, Isolated Logic)]:::unit
    Integration[🔗 Integration<br/>(DB, EdgeRAG Retrieval)]:::int
    E2E[🌍 End-to-End<br/>(Agents + MQTT + Frontend)]:::e2e
    
    Unit --> Integration
    Integration --> E2E
    
    classDef e2e fill:#ffebee,stroke:#c62828,color:#b71c1c
    classDef int fill:#fff3e0,stroke:#e65100,color:#e65100
    classDef unit fill:#e3f2fd,stroke:#1565c0,color:#0d47a1
```

## 🧩 Test Modularity

### `backend/`
- Testing the execution flow of the **LangGraph** orchestrator.
- Validating the determinism of the **Dijkstra** routing algorithm in the Referral Agent.
- Mocking the `llama.cpp` inference engine to verify that the Diagnosis Agent correctly parses edge-case IMCI RAG context.

### `cloud/`
- Verifying that the Flower Server correctly handles malformed client gradients (simulating a Byzantine/compromised PHC node using `test_strategy.py`).

### `ml/`
- Running assertions on the data harmonizer scripts to ensure that raw MIMIC-IV extraction correctly maps to the AyushBot `PatientState` schema.

## 🛠️ Execution

The global testing suite is managed by `pytest` at the root.

```bash
# Run all fast, isolated unit tests
make test

# Run the complete test suite including slow LLM integration mocks
pytest tests/ --runslow

# Generate coverage report
pytest --cov=backend --cov-report=html
```

## 🛡️ Clinical Validation Protocols
All changes to the Agentic prompts or the ML triage thresholds absolutely require a passing test suite and a manual sign-off against the WHO IMCI Chart Booklet specifications.
