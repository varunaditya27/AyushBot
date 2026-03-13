<div align="center">

# 📈 Signal Quality Analytics

**Post-Hoc Pipeline for Motion Artifact Correction**

</div>

## 📌 Overview

The `/ml/signal_quality` directory sits exactly between the firmware hardware tier and the central classification logic. While the physical sensor pack (`/firmware/edge_impulse`) executes tiny ML models to reject wildly noisy readings in real-time, this module focuses on complex offline processing of retained photoplethysmogram (PPG) waveforms to extract latent physiological features.

## ⚙️ Waveform Processing Pipeline

Rather than trusting single-point estimates (e.g., "SpO2 = 91%"), the scripts here process massive time-series buffers of optical data (Red/IR LED voltages) to isolate and reconstruct clean cardiac cycles despite persistent child squirming.

```mermaid
graph TD
    RawCSV[(Raw PPG Arrays<br/>from Sensors)]:::raw
    
    subgraph DSP Operations
        Bandpass[Butterworth Bandpass Filter<br/>(0.5Hz - 5.0Hz)]:::dsp
        Morphology[Peak / Trough Detection]:::dsp
        SQI[Signal Quality Indexing<br/>(Template Matching)]:::sqi
        
        RawCSV --> Bandpass
        Bandpass --> Morphology
        Morphology --> SQI
    end
    
    subgraph Model Training
        ResNet[1D ResNet Autoencoder<br/>Denoise Training]:::ml
    end
    
    SQI --> ResNet
    
    classDef raw fill:#e8eaf6,stroke:#3f51b5
    classDef dsp fill:#e3f2fd,stroke:#1565c0
    classDef sqi fill:#fff3e0,stroke:#e65100
    classDef ml fill:#e8f5e9,stroke:#2e7d32
```

## 🧩 Scripts

- **`ppg_filtering.py`**: Implements 4th-order Butterworth filters to strip out high-frequency ambient light noise and low-frequency baseline wandering (breathing artifacts).
- **`sqi_extractor.py`**: Computes heuristic SQI metrics (Skewness, Kurtosis, Perfusion Index) quantifying the clinical reliability of a specific 5-second sampling window.
- **`denoise_autoencoder.py`**: Code defining a PyTorch 1D Convolutional Autoencoder architecture deployed strictly for academic research into signal reconstruction (not currently utilized in real-time edge gateways).

## 🛠️ Data Handling
The scripts in this directory consume enormous CSVs representing raw LED ADC sweeps. Ensure your environment has at least 16GB of RAM before running bulk transformations.
