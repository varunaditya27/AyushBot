<div align="center">

# 📖 Edge RAG

**Retrieval-Augmented Generation for IMCI Guidelines**

</div>

## 📌 Overview

The `/backend/rag` directory implements the context engine that grounds the LLM in real-world clinical rules. Because raw LLMs hallucinate, AyushBot utilizes a vector-database-backed retrieval system to inject verbatim WHO IMCI (Integrated Management of Childhood Illness) protocols directly into the prompt context before inference.

## 🏗️ Retrieval Topology

```mermaid
graph LR
    Query[Patient Symptoms<br/>'Cough, fast breathing']:::input

    subgraph "RAG Engine"
        Embed[MiniLM-L6-v2<br/>ONNX Execution]:::embed
        FAISS[(FAISS Index<br/>IVF_Flat)]:::db
        Rank[Cross-Encoder<br/>Reranking]:::rank

        Query --> Embed
        Embed --> FAISS
        FAISS --> Rank
    end

    Context[IMCI Section 3.2:<br/>'Pneumonia classification']:::out

    Rank --> Context

    classDef input fill:#e3f2fd,stroke:#1565c0
    classDef embed fill:#f3e5f5,stroke:#7b1fa2
    classDef db fill:#fff3e0,stroke:#e65100
    classDef rank fill:#e8f5e9,stroke:#2e7d32
    classDef out fill:#ffebee,stroke:#c62828
```

## 🧩 Architectural Decisions

### `retriever.py`

To save RAM on the gateway, the embedding model used for vector distance calculation (`all-MiniLM-L6-v2`) is executed via **ONNX Runtime** rather than loading the full PyTorch library.

### `build_index.py`

A build-time script (intended to be run on developers' laptops, not the Pi). It parses the raw PDFs/text inside `/data/assets`, chunks them semantically via LangChain's recursive splitters, and generates the flat `.faiss` artifact that the PHC Gateway will mount.

### Guardrails

Post-retrieval validation logic is embedded in the retriever. If the top cosine similarity score falls below the configured confidence threshold, `guardrail_triggered` is raised and the LLM should be bypassed.

## 🛠️ Indexing Operations

_(Run on local host, NOT edge device)_

```bash
# Update the FAISS index with new WHO guidelines
poetry run python backend/rag/build_index.py --source data/assets/new_guidelines.pdf
```

## ✅ Quick Smoke Test

```bash
python backend/rag/smoke_test.py
```
