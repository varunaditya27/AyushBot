<div align="center">

# 📓 ML Notebooks Sandbox

**Exploratory Data Analysis and Feature Engineering**

</div>

## 📌 Overview

The `/ml/notebooks` directory operates strictly as an interactive analytical playground for Data Scientists and Researchers working on the AyushBot project. None of the `.ipynb` files located here are deployed into production or executed by the Edge Gateway infrastructure.

This is where raw datasets from `/data/raw` are probed to uncover correlations dictating pediatric triage thresholds setup in the XGBoost classification module.

## 🔬 Core Notebooks

```mermaid
mindmap
  root((AyushBot<br/>Notebooks))
    Feature Engineering
      [SpO2 vs Temp Non-linearities]
      [Respiratory Rate Extraction]
    Model Explanation
      [SHAP Value Heatmaps<br/>(xgboost_visualize.ipynb)]
      [Partial Dependence Plots]
    Imbalance Handling
      [SMOTE Analysis]
      [Loss Re-weighting]
    Sanity Checks
      [MIMIC-IV Parsing Distributions]
```

## 🧩 Key Explorations

- **`01_vital_interactions.ipynb`**: Explores the statistical interplay between fever and tachycardia in pediatric patients. Crucial for establishing the base logic of the `agent_intake` XGBoost bounds.
- **`02_shap_analysis.ipynb`**: Utilizes SHAP to de-mistify the black-box nature of the XGBoost classifier. This notebook produces the waterfall plots used during clinical presentations to prove to doctors *why* the AI flagged a patient as CRITICAL.
- **`03_anomaly_detection.ipynb`**: An investigation into Isolation Forests and Autoencoders to intercept noisy, spurious signals from the ESP32 sensors *before* they corrupt the downstream agent logic.

## 🛠️ Usage
Since these notebooks rely heavily on visual plotting libraries (`matplotlib`, `seaborn`, `shap`):
```bash
poetry shell
cd ml/notebooks
jupyter lab
```
