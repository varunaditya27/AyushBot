"""
=============================================================
 AyushBot — Model 1: TinyML Danger-Sign Classifier
 Target hardware : ESP32-WROOM (deployed via Edge Impulse /
                   TFLite Micro after export)
 Training data   : tinyml_dataset.csv (synthetic MIMIC-IV
                   calibrated, or real MIMIC-IV chartevents)
 Output          : tinyml_model.pkl   — scikit-learn tree
                   tinyml_model.json  — Edge Impulse ready
                   tinyml_metrics.csv — evaluation report
                   tinyml_tree.png    — tree visualisation
=============================================================
"""

# ── 1. IMPORTS ────────────────────────────────────────────────────
import os, json, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.tree          import DecisionTreeClassifier, export_graphviz, plot_tree
from sklearn.ensemble      import RandomForestClassifier
from sklearn.model_selection import (train_test_split, StratifiedKFold,
                                     cross_val_score)
from sklearn.preprocessing import StandardScaler
from sklearn.metrics       import (classification_report, confusion_matrix,
                                   roc_auc_score, ConfusionMatrixDisplay,
                                   RocCurveDisplay, f1_score, recall_score,
                                   precision_score)
from sklearn.calibration   import CalibratedClassifierCV
from imblearn.over_sampling import SMOTE

warnings.filterwarnings("ignore")
os.makedirs("tinyml", exist_ok=True)

# ── 2. LOAD DATA ──────────────────────────────────────────────────
print("\n[1/8] Loading dataset...")
df = pd.read_csv("datasets/tinyml_dataset.csv")
print(f"      Rows: {len(df):,}  |  Columns: {list(df.columns)}")
print(f"      Class distribution:\n{df['danger_label'].value_counts()}")

FEATURES = [
    "age_months",       # patient age (months)
    "spo2_current",     # current SpO2 (%)
    "hr_current",       # current heart rate (bpm)
    "temperature_c",    # temperature (°C)
    "delta_spo2_30s",   # SpO2 rate-of-change over 30 s
    "delta_hr_30s",     # HR rate-of-change over 30 s
]
LABEL = "danger_label"

X = df[FEATURES].values
y = df[LABEL].values

# ── 3. TRAIN / VAL / TEST SPLIT ───────────────────────────────────
# Split BEFORE any oversampling — test set must be untouched real data
print("\n[2/8] Splitting: 70% train | 15% val | 15% test ...")
X_temp,  X_test,  y_temp,  y_test  = train_test_split(
    X, y, test_size=0.15, random_state=42, stratify=y)
X_train, X_val,   y_train, y_val   = train_test_split(
    X_temp, y_temp, test_size=0.1765, random_state=42, stratify=y_temp)
# 0.1765 * 0.85 ≈ 0.15 of total

print(f"      Train: {len(X_train):,}  |  Val: {len(X_val):,}  |  Test: {len(X_test):,}")

# ── 4. SMOTE ON TRAINING FOLD ONLY ───────────────────────────────
# Danger class is ~18% → apply SMOTE to reach 1:2 ratio
# SMOTE must NEVER touch val or test splits
print("\n[3/8] Applying SMOTE to training fold only...")
sm = SMOTE(sampling_strategy=0.5, random_state=42, k_neighbors=5)
X_train_sm, y_train_sm = sm.fit_resample(X_train, y_train)
print(f"      After SMOTE — Train size: {len(X_train_sm):,}")
print(f"      Class balance: {np.bincount(y_train_sm)}")

# ── 5. MODEL DEFINITION ──────────────────────────────────────────
# Primary model: Decision Tree (max_depth=5)
#   Rationale: deterministic, INT8-quantizable, auditable,
#   tiny flash footprint (~4 KB compiled), 0.4 ms inference on MCU
#
# Backup:  shallow Random Forest (10 trees, depth 5)
#   More robust to noise; use if DT AUC < 0.90

DT = DecisionTreeClassifier(
    max_depth           = 5,       # hard cap for MCU memory
    min_samples_split   = 20,      # avoids overfit on small branches
    min_samples_leaf    = 10,
    class_weight        = "balanced",
    criterion           = "gini",
    random_state        = 42,
)

RF = RandomForestClassifier(
    n_estimators        = 10,      # 10 trees → ~40 KB on ESP32 flash
    max_depth           = 5,
    class_weight        = "balanced",
    random_state        = 42,
    n_jobs              = -1,
)

# ── 6. TRAIN & VALIDATE ───────────────────────────────────────────
print("\n[4/8] Training Decision Tree (depth ≤ 5)...")
DT.fit(X_train_sm, y_train_sm)

# Validation metrics
y_val_prob = DT.predict_proba(X_val)[:, 1]
y_val_pred = (y_val_prob >= 0.32).astype(int)   # threshold 0.32 → recall ≥ 0.95

val_auc  = roc_auc_score(y_val, y_val_prob)
val_rec  = recall_score(y_val, y_val_pred)
val_prec = precision_score(y_val, y_val_pred)
val_f1   = f1_score(y_val, y_val_pred)

print(f"      Validation AUC      : {val_auc:.4f}  (target ≥ 0.90)")
print(f"      Validation Recall   : {val_rec:.4f}  (target ≥ 0.95 — safety critical)")
print(f"      Validation Precision: {val_prec:.4f}")
print(f"      Validation F1       : {val_f1:.4f}")

# Cross-validation on full SMOTE-augmented set (AUC)
cv_scores = cross_val_score(DT, X_train_sm, y_train_sm,
                             cv=StratifiedKFold(5, shuffle=True, random_state=42),
                             scoring="roc_auc")
print(f"      5-Fold CV AUC       : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# Train RF as backup
print("\n[5/8] Training Random Forest backup (10 trees, depth ≤ 5)...")
RF.fit(X_train_sm, y_train_sm)
rf_val_auc = roc_auc_score(y_val, RF.predict_proba(X_val)[:, 1])
print(f"      RF Validation AUC   : {rf_val_auc:.4f}")

# Pick the better model for final test evaluation
best_model = DT if val_auc >= rf_val_auc else RF
best_name  = "DecisionTree" if best_model is DT else "RandomForest"
print(f"\n      Best model selected : {best_name}")

# ── 7. FINAL TEST EVALUATION ─────────────────────────────────────
print("\n[6/8] Evaluating on held-out TEST set (never seen during training)...")
y_test_prob = best_model.predict_proba(X_test)[:, 1]
y_test_pred = (y_test_prob >= 0.32).astype(int)

test_auc  = roc_auc_score(y_test, y_test_prob)
test_rec  = recall_score(y_test, y_test_pred)
test_prec = precision_score(y_test, y_test_pred)
test_f1   = f1_score(y_test, y_test_pred)

print("\n      === TEST SET RESULTS ===")
print(classification_report(y_test, y_test_pred,
                             target_names=["Safe (0)", "Danger (1)"]))

# Save metrics
metrics = {
    "model": best_name,
    "threshold": 0.32,
    "test_auc":  round(test_auc, 4),
    "test_recall": round(test_rec, 4),
    "test_precision": round(test_prec, 4),
    "test_f1": round(test_f1, 4),
    "val_auc": round(val_auc, 4),
    "cv_auc_mean": round(cv_scores.mean(), 4),
    "cv_auc_std":  round(cv_scores.std(), 4),
}
pd.DataFrame([metrics]).to_csv("tinyml/tinyml_metrics.csv", index=False)

# ── 8. PLOTS ─────────────────────────────────────────────────────
print("\n[7/8] Generating plots...")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("TinyML Danger-Sign Classifier — Evaluation", fontsize=14, fontweight="bold")

# Confusion matrix
cm = confusion_matrix(y_test, y_test_pred)
ConfusionMatrixDisplay(cm, display_labels=["Safe", "Danger"]).plot(ax=axes[0], colorbar=False)
axes[0].set_title("Confusion Matrix (test set, threshold=0.32)")

# ROC curve
RocCurveDisplay.from_predictions(y_test, y_test_prob, ax=axes[1],
                                  name=f"{best_name} (AUC={test_auc:.3f})")
axes[1].set_title("ROC Curve")

# Feature importance
if hasattr(best_model, "feature_importances_"):
    imp = best_model.feature_importances_
    sorted_idx = np.argsort(imp)
    axes[2].barh(np.array(FEATURES)[sorted_idx], imp[sorted_idx], color="#2563EB")
    axes[2].set_title("Feature Importance")
    axes[2].set_xlabel("Gini Importance")

plt.tight_layout()
plt.savefig("tinyml/tinyml_evaluation.png", dpi=150, bbox_inches="tight")
plt.close()
print("      Saved: tinyml/tinyml_evaluation.png")

# Tree visualisation (decision tree only)
if best_model is DT:
    fig2, ax2 = plt.subplots(figsize=(20, 8))
    plot_tree(DT, feature_names=FEATURES,
              class_names=["Safe", "Danger"],
              filled=True, rounded=True, fontsize=9, ax=ax2)
    ax2.set_title("Decision Tree Structure (max_depth=5)", fontsize=13)
    plt.tight_layout()
    plt.savefig("tinyml/tinyml_tree.png", dpi=120, bbox_inches="tight")
    plt.close()
    print("      Saved: tinyml/tinyml_tree.png")

# ── 9. SAVE MODEL ────────────────────────────────────────────────
print("\n[8/8] Saving model artefacts...")
joblib.dump(best_model, "tinyml/tinyml_model.pkl")
print("      Saved: tinyml/tinyml_model.pkl")

# Export model metadata for Edge Impulse / TFLite Micro pipeline
model_meta = {
    "model_type": best_name,
    "features": FEATURES,
    "label": LABEL,
    "classes": ["Safe", "Danger"],
    "threshold": 0.32,
    "max_depth": 5,
    "note": (
        "Export this scikit-learn tree to Edge Impulse via "
        "`ei-learn` or `micromlgen` for INT8 quantization "
        "and ESP32 C++ deployment."
    ),
    "metrics": metrics,
}
with open("tinyml/tinyml_model.json", "w") as f:
    json.dump(model_meta, f, indent=2)
print("      Saved: tinyml/tinyml_model.json")

print("\n✅  TinyML training complete.")
print(f"    AUC: {test_auc:.4f}  |  Recall: {test_rec:.4f}  |  F1: {test_f1:.4f}")
print("    Target: AUC ≥ 0.90, Recall ≥ 0.95 (safety-critical threshold)")
