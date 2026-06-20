# Backend Testing

Run commands from the repository root.

## Baseline Checks

```bash
python3 -m compileall -q backend
.venv/bin/pytest backend/tests tests/unit -q
```

## Dependency Tiers

Pure unit and safety tests:

```bash
.venv/bin/pytest \
  backend/tests/test_config_behavior.py \
  backend/tests/test_language_agent.py \
  backend/tests/test_orchestrator_state.py \
  backend/tests/test_clinical_reference_policy.py \
  backend/tests/test_rag_artifacts.py \
  backend/tests/test_fl_safety.py \
  backend/tests/test_optional_import_stability.py \
  tests/unit/test_agent_diagnosis.py \
  tests/unit/test_agent_intake.py \
  tests/unit/test_agent_referral.py \
  tests/unit/test_config.py \
  tests/unit/test_dp_mechanism.py \
  tests/unit/test_fl_aggregator.py \
  -q
```

Database and migration tests:

```bash
.venv/bin/pytest \
  backend/tests/test_db_layer.py \
  tests/unit/test_db_crud.py \
  tests/integration/test_db_migrations.py \
  -q
```

API and sync contract tests:

```bash
.venv/bin/pytest \
  backend/tests/test_api_surface.py \
  backend/tests/test_auth_hardening.py \
  tests/unit/test_auth_security.py \
  tests/integration/test_full_pipeline.py \
  tests/integration/test_phase3_contracts.py \
  -q
```

Optional ML/RAG/integration tests:

```bash
.venv/bin/pytest \
  tests/unit/test_rag_pipeline.py \
  tests/integration/test_fl_round.py \
  tests/integration/test_ble_mqtt_stack.py \
  -q
```

These optional tests use `pytest.importorskip` for heavy or service-specific
dependencies such as FAISS, BM25, Flower, and Paho MQTT.

## Strongest Local Backend Suite

```bash
python3 -m compileall -q backend
.venv/bin/pytest backend/tests tests/unit tests/integration -q
```

The root `pytest.ini` defaults to `tests/`, so include `backend/tests`
explicitly when running the full backend suite.
