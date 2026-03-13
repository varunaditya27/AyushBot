# =============================================================================
# AyushBot Tests — Simulation: ASHA Worker Scenario Runner
# =============================================================================
#
# PURPOSE:
#   End-to-end simulation of realistic ASHA worker interaction scenarios.
#   Unlike integration tests (which mock the LLM), simulation tests run
#   with real models loaded and simulate the full user experience.
#
# IMPORTANT:
#   Simulation tests are SLOW (require loading Phi-3 Mini + FAISS index)
#   and require a machine with sufficient RAM (>= 8 GB). They are NOT
#   run in CI — only on developer machines or dedicated test hardware.
#   Mark with @pytest.mark.slow and @pytest.mark.simulation.
#
# SCENARIOS:
#
#   scenario_01_severe_pneumonia
#     Background: ASHA in rural Rajasthan evaluates a 14-month-old girl
#     Vitals: SpO2=88%, HR=160, Temp=39.8°C, Weight=7.0 kg
#     Symptoms (in Hindi): "bachchi ki saans bahut tez chal rahi hai,
#       chhati andar ja rahi hai, peena band kar diya hai"
#     Expected flow:
#       - Language Agent translates Hindi → English
#       - Intake Agent classifies as CRITICAL
#       - Diagnosis Agent: Severe pneumonia as top differential
#       - Referral Agent: Emergency referral to District Hospital +
#         pre-referral: Amoxicillin first dose + oxygen if available
#       - Language Agent translates action plan back to Hindi
#     Evaluation: Clinical correctness reviewed by a medical expert
#
#   scenario_02_mild_diarrhea
#     Background: ASHA in Bihar evaluates a 3-year-old boy
#     Vitals: All normal
#     Symptoms (in Hindi): "bachche ko kal se dast ho rahe hain,
#       thoda paani peeta hai, khana kha raha hai"
#     Expected: LOW risk, home management with ORS
#
#   scenario_03_malaria_suspicion
#     Background: ASHA in Chhattisgarh tribal area, monsoon season
#     Vitals: Temp=40.0°C, SpO2=94%, HR=150
#     Symptoms: High fever with chills, 3 days
#     Expected: HIGH risk (malaria-endemic area), referral for rapid
#       diagnostic test, pre-referral antimalarial if indicated
#
#   scenario_04_sensor_failure_mid_assessment
#     Background: During assessment, SpO2 sensor disconnects
#     Expected: System notifies ASHA of sensor failure, continues
#       assessment with available data, flags reduced confidence
#
#   scenario_05_offline_fl_sync
#     Background: Gateway has been offline for 7 days
#     Expected: Gossip sync with a neighboring PHC gateway (if available),
#       queue gradient upload for when cloud reconnects
#
# OUTPUT:
#   - Scenario narratives with actual model outputs (for human review)
#   - Latency measurements per agent
#   - Clinical correctness checklist (manual sign-off required)
# =============================================================================
