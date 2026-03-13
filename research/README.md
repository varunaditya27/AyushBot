<div align="center">

# 🔬 AyushBot Research Hub

**Incubator for Prompts, Experiments, and Prototyping**

</div>

## 📌 Overview

The `/research` directory is a sandbox explicitly separated from the production `/backend` code. This is where experimental Jupyter Notebooks, raw evaluation data for offline RAG benchmarking, and prompt engineering scratchpads live.

**Nothing in this directory is deployed to the PHC Gateway.**

## 🧪 Ongoing Explorations

```mermaid
graph TD
    %% Pillars
    Prompting[📝 Prompt Engineering<br/>(System Prompts, Few-Shot)]:::pillar
    Benchmarking[📊 RAG Evaluation<br/>(Context Recall, Hallucination)]:::pillar
    Synthesis[🤖 Audio Synthesis<br/>(Indic TTS fidelity)]:::pillar
    
    %% Output
    Production((Production `/backend`)):::prod
    
    Prompting --> Production
    Benchmarking --> Production
    Synthesis --> Production
    
    classDef pillar fill:#f3e5f5,stroke:#7b1fa2
    classDef prod fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#1b5e20
```

## 🧩 Modularity Breakdown

### `notebooks/`
The playground for isolated ML and data visualization tasks.
- **`rag_eval_phi3.ipynb`**: Execution of RAGAS (RAG Assessment) metrics on the quantized Phi-3 model using the FAISS IMCI index to quantify hallucination rates prior to release.
- **`xgboost_feature_importance.ipynb`**: Detailed SHAP value visualizations exploring *why* the `agent_intake` flags certain combinations of SpO2 and fever as CRITICAL.

### `prompts/`
Version-controlled plain text prompts used to instruct the LangGraph agents.
- Exploring zero-shot vs in-context learning constraints for the lightweight edge LLM.

### `hardware_prototyping/`
Schematics, CAD models (if applicable), and raw validation scripts for tuning the I2C polling rates of the MAX30102 on breadboards before moving logic to the `/firmware` C++ pipeline.

## 🛠️ Environment

Because this directory involves heavy data analysis:

```bash
# Enter the root virtual environment
poetry shell

# Spin up the notebook server
cd research
jupyter lab
```
