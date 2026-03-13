<div align="center">

# 🧬 Synthetic Data Generator

**Simulating Rural Telemetry for Load Testing**

</div>

## 📌 Overview

The `/data/synthetic` directory contains scripts and the resulting outputs used to generate artificial patient encounters. Because acquiring massive, labeled datasets of pediatric vitals from rural Indian PHCs is logistically and ethically difficult (due to HIPAA/DPDP Act constraints), AyushBot uses controlled synthetic data to bootstrap the XGBoost triage classifier and stress-test the hardware.

## 🧪 Simulation Strategies

### 1. Bootstrapping the ML Pipeline
Using statistical distributions extracted from the public **MIMIC-IV** dataset, scripts in this folder generate CSVs containing millions of simulated pediatric vitals (Heart Rate, SpO2, Temperature). Crucially, the scripts inject explicit anomalies (e.g., simulating a 3-year-old with an SpO2 of 88% and respiratory rate of 55) to ensure the `agent_intake` correctly flags them as `CRITICAL`.

### 2. MQTT Load Testing
To verify the Raspberry Pi 4 Gateway won't crash when dozens of Android tablets sync offline cases simultaneously, we synthesize heavy JSON payloads tracking the exact Room database schema.

```mermaid
graph LR
    Generator[Generator Script<br/>(Gaussian distributions)]:::gen
    
    SynCSV[(synthetic_vital_waves.csv)]:::csv
    SynJSON[(synthetic_sync_payloads.json)]:::json
    
    XGBoost[XGBoost Tuning<br/>(/ml)]:::ml
    Mosquitto[MQTT Broker<br/>(/infra)]:::mq
    
    Generator --> SynCSV
    Generator --> SynJSON
    
    SynCSV --> XGBoost
    SynJSON -.->|"Load Test"| Mosquitto
    
    classDef gen fill:#f3e5f5,stroke:#7b1fa2
    classDef csv fill:#e3f2fd,stroke:#1565c0
    classDef json fill:#e3f2fd,stroke:#1565c0
    classDef ml fill:#e8f5e9,stroke:#2e7d32
    classDef mq fill:#fff3e0,stroke:#e65100
```

## 🛠️ Execution

To generate a fresh batch of 100,000 synthetic patient records with 15% enforced anomalies:

```bash
cd data/synthetic
poetry run python generate_cohort.py --records 100000 --anomaly-rate 0.15
```
