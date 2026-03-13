<div align="center">

# 🎯 Triage Classifier Training

**The Offline XGBoost Foundry**

</div>

## 📌 Overview

The `/ml/triage_classifier` directory is the core data science engine of AyushBot. It holds the end-to-end Python pipeline that transforms massive, unstructured clinical datasets into the highly optimized, explainable **XGBoost Tree `.json` artifact** utilized by the `agent_intake.py` node on the Raspberry Pi gateways.

## ⚙️ Training Flow

Creating a clinically safe triage model requires heavily scrutinized steps.

```mermaid
graph LR
    subgraph Data Harmonization
        Extract[01_extract_mimic.py]:::data
        Clean[02_clean_anomalies.py]:::data
        Impute[03_impute_missing.py]:::data
        
        Extract --> Clean --> Impute
    end
    
    subgraph Model Training
        Train[04_train_xgb.py<br/>Grid Search CV]:::train
        Eval[05_evaluate.py<br/>PR-AUC / SHAP]:::eval
        Export[06_export_json.py]:::export
        
        Impute --> Train
        Train --> Eval
        Eval --> Export
    end
    
    Final([gateway_intake_v2.json]):::artifact
    
    Export --> Final
    
    classDef data fill:#e3f2fd,stroke:#1565c0
    classDef train fill:#f3e5f5,stroke:#7b1fa2
    classDef eval fill:#fff3e0,stroke:#e65100
    classDef export fill:#e8f5e9,stroke:#2e7d32
    classDef artifact fill:#ffebee,stroke:#c62828,color:#b71c1c,stroke-width:2px
```

## 🧩 Pipeline Components

- **`01_extract_mimic.py`**: Cross-references patient admission demographics with ICU charting events to isolate pediatric populations (0-5 years) presenting with respiratory/fever symptoms.
- **`04_train_xgb.py`**: Orchestrates hyperparameter search. It implements massive class weighting because `CRITICAL` state encounters represent less than 5% of all triage cases. Accurate identification of minorities is crucial.
- **`05_evaluate.py`**: Generates confusion matrices mapping against WHO IMCI ground truth classifications, not just the model's raw probability logs.
- **`06_export_json.py`**: Converts the Scikit-learn/XGBoost object into a universally readable `.json` graph of decision trees for native parsing via `xgboost.Booster()` on the edge gateway without requiring massive ML libraries.

## 🛠️ Execution Context
Due to the sheer number of grid search fits (500+ iterations), running the complete pipeline from 01 through 06 is computationally intensive and should be handled on cloud instances with multi-core CPUs.
