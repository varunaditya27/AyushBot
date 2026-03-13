<div align="center">

# 🏥 AyushBot: Clinical Triage & Navigation System

**Empowering ASHA Workers with Offline-First, AI-Driven Clinical Support**

[![Kotlin](https://img.shields.io/badge/Kotlin-2.0-blue.svg?logo=kotlin)](#)
[![Python](https://img.shields.io/badge/Python-3.11-yellow.svg?logo=python)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg?logo=fastapi)](#)
[![Jetpack Compose](https://img.shields.io/badge/Compose-Material%203-4285F4.svg?logo=android)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#)

</div>

## 📖 Introduction

AyushBot is a unified hardware-software ecosystem designed specifically for rural Indian healthcare environments. By combining a low-cost vital sensor pack, an edge-hosted local LLM/RAG pipeline (Raspberry Pi 4 gateway), and an offline-first Android application, AyushBot enables Accredited Social Health Activists (ASHAs) to conduct high-quality, evidence-based triage without requiring persistent internet connectivity.

## 🏗️ System Architecture

This monorepo is divided into specialized modular components:

```mermaid
graph TD
    %% Core Nodes
    A[📱 Android App<br/>Offline-First / Voice UX]:::app
    B[📡 PHC Gateway<br/>RPi 4 / Edge RAG / API]:::gateway
    C[☁️ Cloud Server<br/>Federated Learning / Sync]:::cloud
    D[📟 Sensor Pack<br/>ESP32 / MAX30102 / MLX90614]:::firmware
    
    %% Relationships
    A <-- "BLE (GATT)" --> D
    A <-- "MQTT (Local Sync/Triage)" --> B
    B <-- "HTTPS / DTN (Async Sync)" --> C
    
    %% Styling
    classDef app fill:#e0f7fa,stroke:#006874,stroke-width:2px,color:#004d40;
    classDef gateway fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#e65100;
    classDef cloud fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#1a237e;
    classDef firmware fill:#f1f8e9,stroke:#33691e,stroke-width:2px,color:#1b5e20;
```

## 📂 Repository Structure

Each directory represents a decoupled component of the system. Click on any directory below to dive into its detailed documentation:

| Directory | Core Purpose | Technologies |
| :--- | :--- | :--- |
| **[`/android`](android/README.md)** | 📱 The ASHA tablet interface, managing local state, UI, and BLE sensor pairing | Kotlin, Jetpack Compose, Room, WorkManager |
| **[`/backend`](backend/README.md)** | 🧠 Edge gateway logic (RPi 4) executing LLM/RAG, Agentic protocols, and MQTT ingestion | Python, FastAPI, LangGraph, EdgeRAG, XGBoost |
| **[`/cloud`](cloud/README.md)** | ☁️ Central server orchestrating cross-PHC Federated Learning and model aggregation | Python, Flower (FL), Docker |
| **[`/firmware`](firmware/README.md)** | 📟 Embedded C++ for the wearable sensor pack handling raw physiological signal capture | PlatformIO, C++, TinyML (TFLite Micro) |
| **[`/ml`](ml/README.md)** | 📈 Offline model training pipelines and data processing scripts for XGBoost risk markers | Scikit-learn, XGBoost, Pandas, Jupyter |
| **[`/infra`](infra/README.md)** | 🛠️ Deployment scripts and Docker configurations for reproducible deployments | Docker Compose, Shell, Mosquitto, Redis |
| **[`/docs`](docs/README.md)** | 📚 Master documentation, design specs, user guides, and architecture decision records | Markdown, Mermaid |
| **[`/data`](data/README.md)** | 🏥 Local storage directory mapped to `.gitignore` for managing raw ingestion datasets | Parquet, SQLite, Medical text corpus |
| **[`/research`](research/README.md)** | 🔬 Scratchpad for experimental notebook analysis, LLM prompt tuning, and hardware prototyping | Jupyter, PyTorch |
| **[`/tests`](tests/README.md)** | 🧪 Integration, unit, and end-to-end tests across all micro-components | Pytest, JUnit, Espresso |

## 🚀 Quick Start

To bootstrap the local development environment:

```bash
# 1. Install dependencies via poetry
make install

# 2. Start the local gateway (Redis, Mosquitto, FastAPI)
make dev-gateway

# 3. In a separate terminal, run Android UI
cd android && ./gradlew installDebug
```

For advanced deployment instructions, refer to the [`/infra` documentation](infra/README.md).

## 🛡️ License

AyushBot is released under the MIT License. See `LICENSE` for more information.