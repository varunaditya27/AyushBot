# =============================================================================
# AyushBot ML — Triage Classifier: Step 5 — Evaluation
# =============================================================================
#
# PURPOSE:
#   Comprehensive evaluation of the trained XGBoost triage classifier on the
#   held-out test set. Generates metrics, visualizations, and a model report
#   that must be reviewed before deployment.
#
# EVALUATION METRICS:
#
#   1. Classification Metrics (per-class and macro-averaged):
#      - Accuracy: Overall correct predictions / total predictions
#      - Precision: Of predicted CRITICALs, how many are truly CRITICAL
#      - Recall (Sensitivity): Of actual CRITICALs, how many were caught
#      - F1 Score: Harmonic mean of precision and recall
#      - Specificity: Of actual non-CRITICALs, how many were correctly
#        classified as non-CRITICAL
#
#   2. CRITICAL-Class Prioritization
#      For clinical safety, the most important metric is:
#        RECALL for CRITICAL class ≥ 95%
#      Missing a CRITICAL case (false negative) is a potentially fatal error.
#      The model should err on the side of over-triaging to CRITICAL rather
#      than under-triaging. This is enforced by adjusting the classification
#      threshold if recall is insufficient.
#
#   3. Confusion Matrix
#      4×4 matrix showing prediction vs. actual for all risk levels.
#      Visualized as a heatmap. Key cells to inspect:
#        - CRITICAL predicted as LOW (worst error — must be near zero)
#        - LOW predicted as CRITICAL (acceptable over-triage, but impacts
#          referral volume)
#
#   4. Calibration
#      Reliability diagram: Does the model's confidence match its accuracy?
#      If the model says "80% probability of CRITICAL," is it correct ~80%
#      of the time? Calibration is important for downstream decision-making.
#
#   5. Fairness Audit
#      Check that model performance does not vary significantly by:
#        - Sex (male vs. female children)
#        - Age group (infant vs. toddler vs. older child)
#      Report per-subgroup metrics and flag any disparities > 5%.
#
# DEPLOYMENT GATE:
#   The model is only approved for deployment if:
#     ✓ CRITICAL recall ≥ 95%
#     ✓ Macro F1 ≥ 0.80
#     ✓ No fairness disparity > 5% across subgroups
#     ✓ Calibration ECE < 0.10
#   If any gate fails, retraining with modified hyperparameters is required.
#
# OUTPUTS:
#   - ml/triage_classifier/model/evaluation_report.json (all metrics)
#   - ml/triage_classifier/model/confusion_matrix.png
#   - ml/triage_classifier/model/calibration_plot.png
#   - ml/triage_classifier/model/fairness_report.json
#
# CLI: python -m ml.triage_classifier.05_evaluate
# =============================================================================
