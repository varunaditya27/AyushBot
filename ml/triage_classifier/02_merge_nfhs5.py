# =============================================================================
# AyushBot ML — Triage Classifier: Step 2 — NFHS-5 Data Merge
# =============================================================================
#
# PURPOSE:
#   Merges India-specific health indicators from the National Family Health
#   Survey (NFHS-5) dataset with the MIMIC-IV triage features to create a
#   training dataset that reflects Indian population health patterns.
#
# WHY NFHS-5:
#   MIMIC-IV is a US hospital dataset — it does not capture the disease
#   distributions, malnutrition prevalence, or vital sign baselines of
#   rural Indian children. NFHS-5 covers 636,000 Indian households with:
#     - Child anthropometry (height, weight, age) → malnutrition indicators
#     - Maternal health indicators
#     - State-level and district-level disease prevalence
#     - Vaccination coverage, anemia prevalence
#
# MERGE STRATEGY:
#   The merge is NOT a simple row join (MIMIC and NFHS have different schemas).
#   Instead, NFHS-5 data is used to:
#
#   1. Initialize Federated Learning Priors
#      Compute state-level baseline statistics from NFHS-5:
#        - Median weight-for-age Z-scores per state
#        - Anemia prevalence per state (affects SpO2 baseline expectations)
#        - Malnutrition rates (stunting, wasting) per state
#      These priors are used to initialize the FL model so that it starts
#      with knowledge of Indian population health norms (rather than US norms).
#
#   2. Augment Training Features
#      For each MIMIC-IV training sample, append synthetic "context features"
#      sampled from NFHS-5 distributions:
#        - Regional malnutrition prevalence (as a background feature)
#        - Regional anemia prevalence
#      This allows the model to learn interactions between vital signs and
#      baseline population health (e.g., SpO2 of 92% is more concerning in
#      a region with high anemia prevalence).
#
#   3. Create Synthetic Indian Samples
#      Generate synthetic training samples using NFHS-5 anthropometry data:
#        - Use NFHS-5 weight/height/age data to compute WHO Z-scores
#        - Pair with synthetic vital signs sampled from clinical distributions
#        - Assign labels based on clinical rules (severe wasting → HIGH risk)
#      These augment the MIMIC-IV data with India-representative samples.
#
# OUTPUTS:
#   - data/processed/merged_triage_features.parquet
#     Combined feature dataset with MIMIC-IV + NFHS-5 augmented samples
#   - data/processed/nfhs5_fl_priors.json
#     State-level baseline statistics for FL initialization
#   - data/processed/merge_metadata.json
#     Merge statistics: record counts, sources, augmentation details
#
# CLI: python -m ml.triage_classifier.02_merge_nfhs5 --nfhs-dir data/raw/nfhs5/
# =============================================================================
