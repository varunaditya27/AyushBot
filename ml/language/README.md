<div align="center">

# 🗣️ Language & Audio Processing

**Bridging the Linguistic Gap for Rural Healthcare**

</div>

## 📌 Overview

The `/ml/language` directory contains the Natural Language Processing (NLP) models, parsers, and Text-to-Speech (TTS) pipelines responsible for localizing AyushBot's generated outputs. 

Because many rural mothers and Accredited Social Health Activists (ASHAs) operate in diverse linguistic environments with varying literacy levels, the `agent_language.py` node leverages these scripts to construct accurate, clinical-grade auditory translations from the English JSON payloads spawned by the `agent_diagnosis.py` LLM.

## 🎙️ NLP Pipeline Architecture

```mermaid
graph TD
    Input[English Action Plan JSON<br/>(from LLM Engine)]:::input
    
    subgraph Localization Engine
        Translate[IndicTrans2<br/>Neural Machine Translation]:::nlp
        IndicTTS[VITS-based TTS<br/>(Hindi/Marathi/etc.)]:::audio
        
        Translate --> IndicTTS
    end
    
    subgraph Quality Assurance
        Dictionary[Clinical Dictionary<br/>(Hardcoded PHC terms)]:::dict
        Translate -.-> Dictionary
    end
    
    Output[Audio .wav + Translated JSON]:::output
    
    Input --> Translate
    IndicTTS --> Output
    
    classDef input fill:#e8f5e9,stroke:#2e7d32
    classDef nlp fill:#e3f2fd,stroke:#1565c0
    classDef dict fill:#fff3e0,stroke:#e65100,stroke-dasharray: 5 5
    classDef audio fill:#f3e5f5,stroke:#7b1fa2
    classDef output fill:#ffebee,stroke:#c62828
```

## 🧩 Components

- **`indic_translation.py`**: Wrapper for loading lightweight Transformer models customized for English-to-Indic clinical language translation. It actively intercepts known medical acronyms (e.g., ORS, PCM, IMCI) to ensure they are transliterated correctly, rather than literally translated.
- **`vits_synthesis.py`**: A localized execution of the **VITS** (Variational Inference with adversarial learning for end-to-end Text-to-Speech) architecture. It synthesizes natural-sounding voice files directly on the Pi 4.
- **`dictionaries/`**: Hardcoded CSV maps mapping complex English medical conditions ("Severe Pneumonia") to culturally appropriate local equivalents to ensure ASHA comprehension.

## 🛠️ Thermal Constraints
Generating audio waveforms via neural networks is computationally heavy. On the Raspberry Pi, VITS inference runs via quantized ONNX to prevent thermal throttling of the overarching LangGraph pipeline.
