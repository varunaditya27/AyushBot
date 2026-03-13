<div align="center">

# 🦟 Mosquitto MQTT Broker

**The Asynchronous Data Spine of the Local PHC Network**

</div>

## 📌 Overview

The `/infra/mosquitto` directory handles the configuration for the Eclipse Mosquitto MQTT broker. This containerized broker acts as the central ingestion point for the AyushBot ecosystem on the Edge Gateway, receiving telemetry from Android tablets and dispatching tasks to the local FastAPI/LangGraph pipeline.

## 📡 Message Routing Topology

AyushBot uses a hierarchical topic structure to ensure clean pub/sub mechanics between dozens of ASHA tablets and the single edge gateway.

```mermaid
graph TD
    Tablet1[📱 ASHA Tablet A]:::tablet
    Tablet2[📱 ASHA Tablet B]:::tablet
    
    Broker((Mosquitto<br/>Broker)):::broker
    
    FastAPI[FastAPI MQTT Worker<br/>(/backend/api/)]:::api
    
    Tablet1 -- "PUB: ayushbot/telemetry/A" --> Broker
    Tablet2 -- "PUB: ayushbot/cases/B" --> Broker
    
    Broker -- "SUB: ayushbot/#" --> FastAPI
    
    FastAPI -- "PUB: ayushbot/response/A" --> Broker
    Broker -- "SUB: ayushbot/response/+" --> Tablet1
    
    classDef tablet fill:#e3f2fd,stroke:#1565c0
    classDef broker fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100
    classDef api fill:#e8f5e9,stroke:#2e7d32
```

## 🧩 Modularity Structure

- **`mosquitto.conf`**: The hardened configuration file. It disables anonymous access, enforces password files, defines the WebSocket listener port (`9001`) and the raw MQTT/TLS listener port (`8883`).
- **`acl.conf`**: Access Control Lists restricting tablets from subscribing to the wildcards (`#`), preventing one ASHA's device from intercepting another's case responses.
- **`password.txt`**: Created dynamically via the `rpi_setup.sh` script; contains hashed credentials for the registered gateway clients.

## 🛠️ Offline Resilience (QoS)
All Android-to-Gateway transmissions use **MQTT QoS 1 or 2 (At least once / Exactly once)**. If the tablet loses WiFi connection to the gateway mid-sync, the persistent session ensures the payloads are retained and re-delivered upon reconnection without duplicating database records.
