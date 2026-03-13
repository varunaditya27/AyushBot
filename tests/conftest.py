# =============================================================================
# AyushBot Tests — Shared Fixtures (conftest.py)
# =============================================================================
#
# PURPOSE:
#   Pytest shared fixtures used across all unit and integration tests.
#   This file is automatically discovered by pytest and its fixtures are
#   available to all test files in the tests/ directory and subdirectories.
#
# FIXTURES TO DEFINE:
#
#   1. sample_patient_state
#      Returns a populated PatientState object (backend/agents/state.py)
#      with realistic sample data for a pediatric patient:
#        - SpO2: 92%, HR: 140 bpm, Temp: 38.5°C, RR: 35
#        - Age: 18 months, Weight: 8.2 kg, Sex: Female
#        - Symptoms: ["fever", "cough", "fast_breathing"]
#        - IMCI danger signs: ["chest_indrawing"]
#
#   2. mock_llm_client
#      Returns a mock LLM inference client that returns deterministic
#      responses without loading the actual Phi-3 model (which is 2+ GB
#      and too slow for unit tests). Configurable response text.
#
#   3. mock_faiss_index
#      Returns a mock FAISS index with a small set of pre-embedded test
#      chunks. Allows testing RAG retrieval logic without building the
#      full index from PDF corpus.
#
#   4. mock_xgboost_model
#      Returns a mock XGBoost model that returns deterministic risk
#      predictions. Used for testing the Intake Agent without loading
#      the trained model file.
#
#   5. sample_sensor_payload
#      Returns a sample MQTT sensor data payload as received from the
#      Arduino sensor pack via the Android bridge:
#        {"device_id": "sensor_001", "timestamp": "...",
#         "spo2": 92, "hr": 140, "temp": 38.5, "status": "ok"}
#
#   6. db_session (integration)
#      Creates a temporary in-memory SQLite database with all tables
#      from backend/db/models.py. Yielded and automatically cleaned up
#      after each test (transaction rollback).
#
#   7. test_config
#      Returns a test-specific configuration dict that overrides
#      backend/config.yaml with test-appropriate values (e.g., reduced
#      DP noise, disabled TLS, mock model paths).
#
# MARKERS:
#   Register custom pytest markers for test categorization:
#     @pytest.mark.slow — Tests taking > 5 seconds (LLM, FL rounds)
#     @pytest.mark.integration — Tests requiring multiple components
#     @pytest.mark.hardware — Tests requiring physical hardware (skip in CI)
# =============================================================================
