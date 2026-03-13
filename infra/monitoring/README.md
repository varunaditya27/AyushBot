<div align="center">

# 📊 Infrastructure Monitoring

**Observability Stack for Edge Gateways**

</div>

## 📌 Overview

The `/infra/monitoring` directory defines the local telemetry gathering tools used to oversee the health of the Raspberry Pi 4 operating in harsh rural conditions (dust, extreme heat, voltage fluctuations).

## 👁️ Telemetry Stack

Because we cannot rely on cloud-hosted dashboards like Datadog, the gateway runs a hyper-lightweight local monitoring stack sidecar alongside the main containers.

```mermaid
graph LR
    subgraph edge [PHC Gateway Hardware]
        Therm[CPU Temp/Freq]:::metric
        RAM[Memory Usage]:::metric
        Docker[Container Health]:::metric
    end
    
    Prometheus[(Prometheus<br/>Local Scraper)]:::db
    Grafana[Grafana<br/>Lightweight Dashboard]:::ui
    
    Therm -.-> Prometheus
    RAM -.-> Prometheus
    Docker -.-> Prometheus
    
    Prometheus --> Grafana
    
    classDef metric fill:#f3e5f5,stroke:#7b1fa2
    classDef db fill:#fff3e0,stroke:#e65100
    classDef ui fill:#e3f2fd,stroke:#1565c0
```

## 🧩 Components

- **`prometheus.yml`**: Defines the scrape intervals (e.g., every 60 seconds) targeting the `node_exporter` endpoint and the FastAPI `/metrics` route to track LLM token generation speeds.
- **`grafana_provisioning/`**: Pre-configured JSON dashboards ensuring the Medical Officer (MO) can instantly view thermal throttling events on the Pi without needing to manually build charts.

## 🌡️ Thermal Throttling Alerts

If the Pi 4 sustains 85°C, the SoC aggressively throttles clock speeds, severely dragging down `llama.cpp` inference speeds (from ~8 tokens/s down to <2 tokens/s). Prometheus is configured to trigger a system-level alert if temperatures ride above 80°C for more than 5 minutes, prompting the MO to adjust the physical placement of the gateway for better airflow.
