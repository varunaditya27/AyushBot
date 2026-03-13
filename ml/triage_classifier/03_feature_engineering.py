# =============================================================================
# AyushBot ML — Triage Classifier: Step 3 — Feature Engineering
# =============================================================================
#
# PURPOSE:
#   Transforms the merged raw features into the final feature vector used
#   for XGBoost training. Also performs train/validation/test splitting,
#   class balancing, and feature normalization.
#
# FEATURE ENGINEERING OPERATIONS:
#
#   1. WHO Z-Score Computation
#      From age_months, sex, and weight_kg, compute:
#        - Weight-for-Age Z-score (WAZ) using WHO 2006 growth standards
#        - If height is available: Height-for-Age Z-score (HAZ)
#      Z-scores quantify malnutrition severity:
#        WAZ < -2 → Underweight
#        WAZ < -3 → Severely Underweight
#
#   2. Vital Sign Deviation Features
#      Compute how far each vital sign deviates from the age-normal range:
#        - SpO2_deficit = 100 - SpO2 (higher = more hypoxic)
#        - HR_deviation = HR - age_normal_HR (accounts for infant tachycardia norms)
#        - Temp_deviation = Temperature - 37.0 (fever assessment)
#        - RR_deviation = RR - age_normal_RR (respiratory rate)
#      Age-normal ranges are loaded from clinical lookup tables (WHO standards).
#
#   3. Composite Risk Indicators
#      Boolean/categorical features from the ASHA checklist items:
#        - danger_sign_count: number of active IMCI danger signs (0-8)
#        - is_malnourished: bool (WAZ < -2)
#        - is_severely_malnourished: bool (WAZ < -3)
#        - has_fever: bool (Temp > 37.5°C)
#        - has_hypoxia: bool (SpO2 < 94%)
#
#   4. Interaction Features
#      XGBoost can learn interactions natively, but explicit interactions
#      help with smaller datasets:
#        - SpO2_deficit × has_fever (fever + hypoxia is more dangerous)
#        - WAZ × danger_sign_count (malnourished + danger signs = high risk)
#
#   5. Train / Validation / Test Split
#      - 70% train, 15% validation, 15% test
#      - Stratified by risk_level to preserve class distribution
#      - No patient overlap between splits (if patient_id is available)
#
#   6. Class Balancing
#      CRITICAL and HIGH cases are rare (~10% of data). Apply:
#        - SMOTE (Synthetic Minority Over-sampling Technique) on the training set
#        - Compute sample weights for XGBoost (inverse class frequency)
#
# OUTPUTS:
#   - data/processed/X_train.parquet, X_val.parquet, X_test.parquet
#   - data/processed/y_train.parquet, y_val.parquet, y_test.parquet
#   - data/processed/feature_metadata.json (feature names, types, statistics)
#   - data/processed/class_weights.json
#
# CLI: python -m ml.triage_classifier.03_feature_engineering
# =============================================================================
