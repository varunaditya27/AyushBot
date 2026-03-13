# =============================================================================
# AyushBot ML — Triage Classifier: Step 1 — MIMIC-IV Data Extraction
# =============================================================================
#
# PURPOSE:
#   Extracts and processes the relevant subset of the MIMIC-IV clinical
#   database for pre-training the XGBoost triage classifier (used by Agent 1).
#
# WHY MIMIC-IV:
#   MIMIC-IV contains 300,000+ de-identified hospital admissions from Beth
#   Israel Deaconess Medical Center. The triage data (ED arrivals with vital
#   signs, acuity scores, and outcomes) provides a rich pre-training signal
#   for learning the mapping: vitals + symptoms → risk level.
#
# EXTRACTION PIPELINE:
#
#   1. Connect to the MIMIC-IV dataset (downloaded to data/raw/mimiciv/)
#      Tables used:
#        - edstays: ED visit records (subject_id, stay_id, intime, outtime)
#        - triage: Triage vitals (temperature, heartrate, resprate, o2sat, sbp, dbp)
#        - vitalsign: Time-series vital signs during ED stay
#        - diagnosis: ICD-10 diagnoses assigned at discharge
#
#   2. Filter to pediatric cohort (age < 18 years) for relevance to AyushBot's
#      primary patient population (children under 5 — but using broader
#      pediatric data for more training samples)
#
#   3. Extract feature columns:
#        - Vital signs at triage: SpO2, HR, Temperature, Respiratory Rate
#        - Demographics: age_months, sex
#        - Visit outcome: hospital admission (yes/no), ICU transfer (yes/no)
#
#   4. Create target labels:
#        Map the ESI (Emergency Severity Index) triage scores to AyushBot's
#        four risk levels:
#          ESI 1 (Resuscitation) → CRITICAL
#          ESI 2 (Emergent)      → HIGH
#          ESI 3 (Urgent)        → MEDIUM
#          ESI 4-5 (Less/Non-urgent) → LOW
#
#   5. Handle missing values:
#        - SpO2 missing: impute with age-specific median
#        - Temperature missing: impute with 36.8°C (normal)
#        - HR missing: impute with age-specific median
#        - Document all imputation decisions in the output metadata
#
#   6. Output to data/processed/mimiciv_triage_features.parquet
#      Also output data/processed/mimiciv_triage_metadata.json with:
#        - Total records extracted
#        - Class distribution (CRITICAL/HIGH/MEDIUM/LOW counts)
#        - Missing value percentages per feature
#        - Age distribution statistics
#
# DATA ACCESS REQUIREMENTS:
#   MIMIC-IV requires PhysioNet credentialed access. The raw data files must
#   be downloaded separately and placed in data/raw/mimiciv/ before running
#   this script. Subject to MIMIC-IV Data Use Agreement.
#
# CLI: python -m ml.triage_classifier.01_extract_mimiciv --mimic-dir data/raw/mimiciv/
# =============================================================================
