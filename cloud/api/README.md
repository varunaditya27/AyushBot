<div align="center">

# 🌐 Cloud Admin API

**Provisioning, Configuration, and Node Management**

</div>

## 📌 Overview

While AyushBot prioritizes offline-first edge triage, the `/cloud/api` directory provides the administrative REST interface for managing the fleet of decentralized Primary Health Center (PHC) Raspberry Pis. It is the control plane for the global network.

## 🛠️ Capabilities

- **Gateway Provisioning (`/nodes/register`)**: Issues the cryptographic Identity certificates required for a new Raspberry Pi to authenticate with the Federated Learning (FL) server.
- **OTA Configuration (`/config/sync`)**: Centralized management of global clinical variables. If the National Health Mission updates triage thresholds, those overrides are pushed here, queued, and propagated to gateways when they next ping the cloud.
- **Health Checks (`/monitoring/status`)**: Tracks the uptime, last-seen timestamps, and thermal throttling states of the decentralized hardware.

## 🧩 Architectural Implementation

```mermaid
graph LR
    Admin[Admin Panel]:::admin
    
    subgraph Cloud API
        Router[FastAPI Routes]:::api
        Postgres[(PostgreSQL<br/>Nodes DB)]:::db
    end
    
    Gateway[Edge Gateway<br/>(Periodic Ping)]:::edge
    
    Admin --> Router
    Router <--> Postgres
    Gateway -.->|"HTTPS DTN"| Router
    
    classDef admin fill:#ffebee,stroke:#c62828
    classDef api fill:#e3f2fd,stroke:#1565c0
    classDef db fill:#fff3e0,stroke:#e65100
    classDef edge fill:#e8f5e9,stroke:#2e7d32
```

## 🔒 Fleet Security (mTLS)

Because the API routes sensitive configuration data:
1. Standard JWTs are insufficient. 
2. The API utilizes **Mutual TLS (mTLS)**.
3. Every endpoint validates that the incoming request is signed by the client certificate issued to that specific hardware MAC address during node registration.

### `routers/node_management.py`
Exposes the CRUD endpoints for managing the lifecycle (Active, Suspended, Maintenance) of registered ASHA Android devices connected to a specific gateway.
