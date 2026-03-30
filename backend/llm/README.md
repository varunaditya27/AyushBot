<div align="center">

# 🧠 Embedded LLM Engine

**Local Inference without the Cloud**

</div>

## 📌 Overview

The `/backend/llm` module encapsulates the local execution of large language models on the hardware constraints of a Raspberry Pi 4 (8GB RAM). It is the cognitive core of the `agent_diagnosis.py` pipeline.

## ⚡ Inference Architecture

To achieve acceptable tokens/second on an ARM Cortex-A72 processor, AyushBot forsakes standard PyTorch/Transformers overhead in favor of pure C++ execution via **`llama.cpp`** Python bindings.

```mermaid
graph TD
    Prompt[Triage Prompt +<br/>RAG Context]:::input

    subgraph "llama.cpp Engine"
        Quant[GGUF Model Weights<br/>4-bit Quantized (Q4_K_M)]:::model
        KV[KV Cache limits<br/>Max 2048 tokens]:::mem
        CPU[ARM NEON<br/>Matrix Math]:::cpu

        Prompt --> Quant
        Quant <--> KV
        Quant <--> CPU
    end

    Output[Action Plan JSON]:::out

    CPU --> Output

    classDef input fill:#e8f5e9,stroke:#2e7d32
    classDef model fill:#fff3e0,stroke:#e65100
    classDef mem fill:#f3e5f5,stroke:#7b1fa2
    classDef cpu fill:#e3f2fd,stroke:#1565c0
    classDef out fill:#ffebee,stroke:#c62828
```

## 🧩 Implementation Details

### `engine.py`

The singleton wrapper for the `Llama` class instantiation.

- Pre-loads the `.gguf` weight file from the `/data/models` volume into RAM during Docker startup to eliminate cold-start latency.
- Enforces strict grammatical structures using **GBNF (GGML BNF)** grammar files. This ensures the LLM output is a perfectly parsable JSON string aligning with the Pydantic schemas expected by the Android tablet, completely eliminating JSON parsing failures.

### `prompts.py`

System prompt templates specifically tuned for small models (like Phi-3 Mini or Llama-3-8B-Instruct). Optimized to prevent the model from "apologizing" or generating conversational filler, forcing direct clinical outputs.

## 🛠️ Hardware Constraints

- **Max Tokens**: The context window is purposefully truncated. Overextending the KV cache will cause the Pi 4 to OOM (Out of Memory) crash.
- **Thermal**: Continuous token generation pegs all 4 CPU cores at 100%. Ensure the physical gateway has active cooling.

## ✅ Quick Smoke Test

```bash
python backend/llm/smoke_test.py
```
