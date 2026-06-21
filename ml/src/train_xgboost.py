"""
=============================================================
 AyushBot — Model 2: XGBoost Pre-Triage Risk Classifier
 Target hardware : Raspberry Pi 4 (gateway layer)
 Training data   : xgboost_dataset.csv (synthetic NFHS-5 +
                   MIMIC-IV calibrated, or real datasets)
 Output          : xgboost_model.pkl      — trained XGBoost
                   xgboost_model.json     — native XGB format
                   xgboost_metrics.csv    — per-class metrics
                   xgboost_evaluation.png — confusion + ROC
                   xgboost_shap.png       — SHAP beeswarm
=============================================================
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────
import os, json, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

import xgboost as xgb

from sklearn.model_selection import (train_test_split, StratifiedKFold,
                                     cross_val_score)
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import (classification_report, confusion_matrix,
                                     ConfusionMatrixDisplay,
                                     roc_auc_score, f1_score)
from imblearn.over_sampling  import SMOTE

warnings.filterwarnings("ignore")
os.makedirs("xgboost", exist_ok=True)

# ── 2. LOAD DATA ──────────────────────────────────────────────────
print("\n[1/9] Loading dataset...")
df = pd.read_csv("datasets/xgboost_dataset.csv")
print(f"      Rows: {len(df):,}  |  Columns: {df.shape[1]}")
print(f"      Class distribution:\n{df['risk_label'].value_counts()}")

# ── 3. DEFINE FEATURE GROUPS ─────────────────────────────────────
# Group A: Direct sensor readings (6 features)
GROUP_A = ["spo2_current", "hr_current", "temperature_c",
           "weight_kg", "hr_spo2_ratio", "ppg_rr_est"]

# Group B: Derived clinical indices (12 features)
GROUP_B = ["age_months", "waz",
           "fast_breathing", "chest_indrawing", "unable_to_drink",
           "convulsions_24h", "pallor", "severe_edema",
           "severe_wasting", "neonate_danger", "prolonged_fever",
           "time_in_field_h"]

# Group C: Temporal trend features (6 features)
GROUP_C = ["delta_spo2_30s", "delta_hr_30s", "spo2_cv",
           "temp_ma3", "hr_iqr", "spo2_variance_flag"]

FEATURES = GROUP_A + GROUP_B + GROUP_C
print(f"\n      Feature groups: A={len(GROUP_A)}  B={len(GROUP_B)}  C={len(GROUP_C)}")
print(f"      Total features : {len(FEATURES)}")

X = df[FEATURES].values

# ── 4. ENCODE LABELS ─────────────────────────────────────────────
# Ordered: Low=0, Medium=1, High=2, Critical=3
label_order = ["Low", "Medium", "High", "Critical"]
le = LabelEncoder()
le.classes_ = np.array(label_order)
y = le.transform(df["risk_label"])
print(f"\n      Label encoding: {dict(zip(label_order, le.transform(label_order)))}")

# ── 5. TRAIN / VAL / TEST SPLIT ───────────────────────────────────
print("\n[2/9] Splitting: 70% train | 15% val | 15% test ...")
X_temp,  X_test,  y_temp,  y_test  = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y)
X_train, X_val,   y_train, y_val   = train_test_split(
    X_temp, y_temp, test_size=0.1765, random_state=42, stratify=y_temp)

print(f"      Train: {len(X_train):,}  |  Val: {len(X_val):,}  |  Test: {len(X_test):,}")
print(f"      Train class counts: {np.bincount(y_train)}")

# ── 6. SMOTE ON TRAINING FOLD ONLY ───────────────────────────────
# High (2) and Critical (3) are under-represented
# SMOTE never applied to val/test splits
print("\n[3/9] Applying SMOTE to training fold (minority classes only)...")
sm = SMOTE(
    sampling_strategy = {2: 1200, 3: 1000},  # upsample High→1200, Critical→1000
    random_state      = 42,
    k_neighbors       = 5,
)
X_train_sm, y_train_sm = sm.fit_resample(X_train, y_train)
print(f"      After SMOTE — Train size : {len(X_train_sm):,}")
print(f"      Class balance: {np.bincount(y_train_sm)}")

# ── 7. XGBOOST MODEL ─────────────────────────────────────────────
# Architecture rationale:
#  - n_estimators=400 with early stopping prevents overfit
#  - max_depth=6: captures non-linear interactions in IMCI features
#  - subsample/colsample: stochastic boosting reduces variance
#  - scale_pos_weight not needed (SMOTE handles imbalance)
#  - use_label_encoder deprecated; eval_metric set explicitly

print("\n[4/9] Defining XGBoost classifier...")
NUM_CLASSES = 4

model = xgb.XGBClassifier(
    objective          = "multi:softprob",
    num_class          = NUM_CLASSES,
    n_estimators       = 400,
    max_depth          = 6,
    learning_rate      = 0.08,
    subsample          = 0.80,
    colsample_bytree   = 0.75,
    min_child_weight   = 5,
    gamma              = 0.1,
    reg_alpha          = 0.3,        # L1 regularization
    reg_lambda         = 1.5,        # L2 regularization
    eval_metric        = ["mlogloss", "merror"],
    early_stopping_rounds = 30,
    random_state       = 42,
    n_jobs             = -1,
    verbosity          = 0,
)

# ── 8. TRAIN WITH EARLY STOPPING ─────────────────────────────────
print("\n[5/9] Training with early stopping (patience=30 rounds)...")
model.fit(
    X_train_sm, y_train_sm,
    eval_set             = [(X_val, y_val)],
    verbose              = 50,
)
best_iter = model.best_iteration
print(f"      Best iteration: {best_iter}")

# ── 9. VALIDATION METRICS ────────────────────────────────────────
print("\n[6/9] Validation metrics...")
y_val_pred  = model.predict(X_val)
y_val_prob  = model.predict_proba(X_val)

val_f1_macro  = f1_score(y_val, y_val_pred, average="macro")
val_f1_weight = f1_score(y_val, y_val_pred, average="weighted")
# One-vs-Rest AUC
val_auc_ovr = roc_auc_score(y_val, y_val_prob, multi_class="ovr", average="macro")

print(f"      Macro F1        : {val_f1_macro:.4f}")
print(f"      Weighted F1     : {val_f1_weight:.4f}")
print(f"      OvR AUC (macro) : {val_auc_ovr:.4f}  (target ≥ 0.82)")

# Cross-validation on combined train+val (AUC macro OvR)
cv_model = xgb.XGBClassifier(
    objective="multi:softprob", num_class=NUM_CLASSES,
    n_estimators=best_iter if best_iter else 200,
    max_depth=6, learning_rate=0.08, subsample=0.80,
    colsample_bytree=0.75, min_child_weight=5,
    gamma=0.1, reg_alpha=0.3, reg_lambda=1.5,
    random_state=42, n_jobs=-1, verbosity=0,
)
cv_auc = cross_val_score(
    cv_model, X_train_sm, y_train_sm,
    cv=StratifiedKFold(5, shuffle=True, random_state=42),
    scoring="roc_auc_ovr_weighted",
)
print(f"      5-Fold CV AUC   : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

# ── 10. FINAL TEST EVALUATION ────────────────────────────────────
print("\n[7/9] Evaluating on held-out TEST set...")
y_test_pred = model.predict(X_test)
y_test_prob = model.predict_proba(X_test)

test_f1_macro  = f1_score(y_test, y_test_pred, average="macro")
test_f1_weight = f1_score(y_test, y_test_pred, average="weighted")
test_auc_ovr   = roc_auc_score(y_test, y_test_prob,
                                multi_class="ovr", average="macro")

print("\n      === TEST SET RESULTS ===")
print(classification_report(y_test, y_test_pred,
                             target_names=label_order))

metrics = {
    "model": "XGBClassifier",
    "best_iteration": int(best_iter) if best_iter else 200,
    "test_f1_macro":  round(test_f1_macro,  4),
    "test_f1_weighted": round(test_f1_weight, 4),
    "test_auc_ovr":   round(test_auc_ovr,   4),
    "val_f1_macro":   round(val_f1_macro,   4),
    "val_auc_ovr":    round(val_auc_ovr,    4),
    "cv_auc_mean":    round(cv_auc.mean(),  4),
    "cv_auc_std":     round(cv_auc.std(),   4),
}
pd.DataFrame([metrics]).to_csv("xgboost/xgboost_metrics.csv", index=False)

# ── 11. PLOTS ─────────────────────────────────────────────────────
print("\n[8/9] Generating evaluation plots...")

# — Confusion Matrix + Feature Importance ————————————————————────
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
fig.suptitle("XGBoost Pre-Triage Classifier — Evaluation", fontsize=14, fontweight="bold")

cm = confusion_matrix(y_test, y_test_pred)
ConfusionMatrixDisplay(cm, display_labels=label_order).plot(
    ax=axes[0], colorbar=True)
axes[0].set_title(f"Confusion Matrix (test set)\nMacro F1={test_f1_macro:.3f}  OvR AUC={test_auc_ovr:.3f}")

# Feature importance (gain)
imp    = model.feature_importances_
idx    = np.argsort(imp)[-20:]          # top 20
colors = ["#DC2626" if f in GROUP_A else
          "#2563EB" if f in GROUP_B else
          "#16a34a" for f in np.array(FEATURES)[idx]]
axes[1].barh(np.array(FEATURES)[idx], imp[idx], color=colors)
axes[1].set_title("Top-20 Feature Importances (Gain)")
axes[1].set_xlabel("Importance")
# Legend
from matplotlib.patches import Patch
legend_el = [Patch(facecolor="#DC2626", label="Group A: Sensor"),
             Patch(facecolor="#2563EB", label="Group B: Clinical"),
             Patch(facecolor="#16a34a", label="Group C: Temporal")]
axes[1].legend(handles=legend_el, loc="lower right", fontsize=9)

plt.tight_layout()
plt.savefig("xgboost/xgboost_evaluation.png", dpi=150, bbox_inches="tight")
plt.close()
print("      Saved: xgboost/xgboost_evaluation.png")

# — SHAP Beeswarm ————————————————————————————————————————————————
print("      Computing SHAP values (optional)...")
try:
    import shap

    explainer = shap.TreeExplainer(model)
    shap_sample = pd.DataFrame(X_test[:400], columns=FEATURES)
    shap_values = explainer.shap_values(shap_sample)

    plt.figure(figsize=(10, 8))
    if isinstance(shap_values, list):
        shap.summary_plot(
            shap_values[3],  # Critical class
            shap_sample,
            plot_type="dot",
            show=False
        )
        plt.title("SHAP Beeswarm — Critical Risk Class")
    else:
        shap.summary_plot(
            shap_values[:, :, 3],
            shap_sample,
            plot_type="dot",
            show=False
        )
        plt.title("SHAP Beeswarm — Critical Risk Class")

    plt.tight_layout()
    plt.savefig("xgboost/xgboost_shap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("      Saved: xgboost/xgboost_shap.png")

except Exception as e:
    print(f"      SHAP skipped due to compatibility issue: {e}")
    print("      Continuing without SHAP. Feature importance plot is still saved.")

# ── 12. SAVE MODEL ───────────────────────────────────────────────
print("\n[9/9] Saving model artefacts...")
joblib.dump(model, "xgboost/xgboost_model.pkl")
model.save_model("xgboost/xgboost_model.json")
print("      Saved: xgboost/xgboost_model.pkl")
print("      Saved: xgboost/xgboost_model.json  (XGBoost native format)")

# Label encoder for inference
joblib.dump(le, "xgboost/xgboost_label_encoder.pkl")
joblib.dump(FEATURES, "xgboost/xgboost_features.pkl")
print("      Saved: xgboost/xgboost_label_encoder.pkl")
print("      Saved: xgboost/xgboost_features.pkl")

# Export inference helper metadata
inference_meta = {
    "model_type": "XGBClassifier",
    "num_classes": NUM_CLASSES,
    "label_order": label_order,
    "features": FEATURES,
    "feature_groups": {
        "A_sensor":   GROUP_A,
        "B_clinical": GROUP_B,
        "C_temporal": GROUP_C,
    },
    "metrics": metrics,
    "note": (
        "Load with xgb.XGBClassifier().load_model('xgboost_model.json'). "
        "For inference: model.predict_proba(X)[0] gives 4-class probability. "
        "SHAP: shap.TreeExplainer(model).shap_values(X) for top-3 features."
    ),
}
with open("xgboost/xgboost_model_meta.json", "w") as f:
    json.dump(inference_meta, f, indent=2)
print("      Saved: xgboost/xgboost_model_meta.json")

print("\n✅  XGBoost training complete.")
print(f"    Macro F1 : {test_f1_macro:.4f}  (target ≥ 0.78)")
print(f"    OvR AUC  : {test_auc_ovr:.4f}  (target ≥ 0.82)")
print(f"    CV AUC   : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")
