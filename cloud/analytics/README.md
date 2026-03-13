<div align="center">

# 📈 Cloud Analytics

**Global Visualization & Epidemiological Dashboards**

</div>

## 📌 Overview

Unlike the local edge gateways, the `/cloud/analytics` directory runs exclusively on the centralized aggregator server. Its purpose is to ingest the metadata arriving alongside federated updates to generate real-time (when connected) epidemiological heatmaps across the entire AyushBot deployment grid.

## 📊 Dashboard Architecture

```mermaid
graph TD
    subgraph Decentralized Edge
        PHC1[PHC Gateway A]:::edge
        PHC2[PHC Gateway B]:::edge
        PHC3[PHC Gateway C]:::edge
    end
    
    subgraph Cloud Aggregator
        Ingest[gRPC Receiver]:::cloud
        Lake[(Time-Series DB<br/>InfluxDB)]:::db
        Dash[Streamlit Dashboard<br/>/cloud/analytics]:::ui
    end
    
    PHC1 -.->|"Anonymized Statistics"| Ingest
    PHC2 -.->|"Anonymized Statistics"| Ingest
    PHC3 -.->|"Anonymized Statistics"| Ingest
    
    Ingest --> Lake
    Lake --> Dash
    
    classDef edge fill:#e8f5e9,stroke:#2e7d32
    classDef cloud fill:#f3e5f5,stroke:#7b1fa2
    classDef db fill:#fff3e0,stroke:#e65100
    classDef ui fill:#e3f2fd,stroke:#1565c0
```

## 🧩 Components

### 1. `ingestion/`
- Handles the parsing of JSON metadata arrays containing high-level stats (e.g., "Total cases this week", "Number of CRITICAL referrals", "Prevalence of cough vs diarrhea").
- **Crucial Rule**: No Personally Identifiable Information (PII) or Protected Health Information (PHI) ever hits this layer. 

### 2. `dashboard.py`
A lightweight **Streamlit** application designed for state-level health officers to monitor the grid.
- Plots interactive Folium map layers showing outbreak clusters.
- Visualizes battery degradation metrics of the ESP32 sensor packs mapped across villages.
- Tracks the drift divergence of the local `agent_intake` models against the global FL aggregated model.

## 🛠️ Running the Dashboard

```bash
cd cloud/analytics
poetry run streamlit run dashboard.py --server.port 8501
```
