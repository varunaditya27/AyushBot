# =============================================================================
# AyushBot ML — Triage Classifier: Model Card
# =============================================================================
#
# MODEL NAME: AyushBot Triage Classifier v1
#
# MODEL TYPE: XGBoost Gradient Boosted Tree Classifier (multi-class)
#
# TASK: Classify pediatric patients into 4 risk levels based on vital signs,
#       symptoms, and demographic features.
#
# OUTPUT CLASSES:
#   - LOW: Home management with ASHA follow-up
#   - MEDIUM: PHC visit within 24 hours
#   - HIGH: CHC/DH visit urgently
#   - CRITICAL: Immediate emergency evacuation
#
# TRAINING DATA:
#   - MIMIC-IV (pediatric ED subset): ~50K+ encounters from US hospital data
#   - NFHS-5 (Indian augmentation): Synthetic Indian-context samples derived
#     from 636K household survey records
#   - Total training samples: ~60K+ (after augmentation and SMOTE balancing)
#   - Data license: MIMIC-IV PhysioNet DUA; NFHS-5 DHS Program open access
#
# INPUT FEATURES (10-15 features):
#   - SpO2, Heart Rate, Temperature, Respiratory Rate (from sensors)
#   - Age (months), Sex (categorical)
#   - Weight-for-Age Z-score (computed from WHO growth standards)
#   - Vital sign deviation features (from age-normal ranges)
#   - IMCI danger sign count (from ASHA checklist)
#   - Composite risk indicators (fever, hypoxia, malnutrition flags)
#
# PERFORMANCE TARGETS:
#   - CRITICAL Recall: ≥ 95% (most important metric for patient safety)
#   - Macro F1: ≥ 0.80
#   - Calibration ECE: < 0.10
#   - Inference latency: < 5 ms on RPi 4 ARM64
#
# KNOWN LIMITATIONS:
#   - Pre-trained on US hospital data; may not fully capture Indian disease
#     distributions until FL adaptation has run for several rounds
#   - Designed for pediatric populations; adult triage may be less accurate
#   - Requires at least SpO2 and Heart Rate to be valid; if both sensors
#     fail, the model cannot produce a reliable prediction
#
# ETHICAL CONSIDERATIONS:
#   - This model SUGGESTS risk levels; it does NOT make clinical decisions
#   - All CRITICAL/HIGH outputs must be confirmed by a qualified doctor
#   - Fairness audit ensures no significant performance disparity by sex or age
#   - Privacy: Model is trained on de-identified data with DP guarantees
#
# DEPLOYMENT:
#   - Primary: ONNX format on RPi 4 gateway (via ONNX Runtime)
#   - Fallback: XGBoost native JSON format
#   - Updated via Federated Learning (new global model every FL round)
# =============================================================================
