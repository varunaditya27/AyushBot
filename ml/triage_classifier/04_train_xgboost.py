# =============================================================================
# AyushBot ML — Triage Classifier: Step 4 — XGBoost Training
# =============================================================================
#
# PURPOSE:
#   Trains the XGBoost gradient-boosted tree classifier that powers Agent 1's
#   risk stratification. This is the primary ML model — it receives the
#   engineered feature vector and outputs a risk level.
#
# WHY XGBOOST:
#   - Excellent performance on tabular data with moderate feature counts
#   - Interpretable: SHAP values provide per-feature explanations
#   - Efficient inference: < 1 ms on Raspberry Pi 4 CPU
#   - Small model size: typically 100 KB - 2 MB (fits in RPi memory alongside
#     the LLM and embedding models)
#   - Handles missing features gracefully (important when sensors fail)
#
# TRAINING PROCEDURE:
#
#   1. Load engineered features from data/processed/ (Step 3 outputs)
#
#   2. Configure hyperparameters:
#        - objective: multi:softprob (4-class classification)
#        - num_class: 4 (LOW, MEDIUM, HIGH, CRITICAL)
#        - max_depth: 6 (prevent overfitting)
#        - learning_rate: 0.1
#        - n_estimators: 200-500 (with early stopping)
#        - subsample: 0.8 (row sampling for regularization)
#        - colsample_bytree: 0.8 (feature sampling)
#        - scale_pos_weight: computed from class weights (Step 3 output)
#
#   3. Train with early stopping on the validation set:
#        - Metric: multi-class log loss
#        - Patience: 20 rounds
#        - This prevents overfitting while finding the optimal tree count
#
#   4. Compute SHAP values on the validation set:
#        - Global feature importance: which features matter most overall
#        - Per-class feature importance: which features drive CRITICAL vs. LOW
#        - Save SHAP summary plots for documentation
#
#   5. Save the trained model:
#        - XGBoost native format: ml/triage_classifier/model/xgb_triage.json
#        - Model metadata: hyperparameters, training metrics, feature list
#
# HYPERPARAMETER TUNING:
#   Optionally run Optuna or grid search for hyperparameter optimization.
#   Tuning space: max_depth [3-8], learning_rate [0.01-0.3], n_estimators
#   [100-1000], subsample [0.6-1.0], colsample_bytree [0.6-1.0].
#
# OUTPUTS:
#   - ml/triage_classifier/model/xgb_triage.json (trained model)
#   - ml/triage_classifier/model/training_metrics.json
#   - ml/triage_classifier/model/shap_importance.json
#   - ml/triage_classifier/model/shap_summary_plot.png
#
# CLI: python -m ml.triage_classifier.04_train_xgboost
# =============================================================================
