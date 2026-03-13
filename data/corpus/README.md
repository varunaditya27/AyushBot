<div align="center">

# 📚 Knowledge Corpus

**The Clinical Source Texts for Edge RAG Indexing**

</div>

## 📌 Overview

The `/data/corpus` directory serves as the raw staging and curation area for all clinical documentation that AyushBot's Edge RAG (Retrieval-Augmented Generation) engine will embed and index. 

This repository of text ensures the LLM generates advice grounded strictly in authorized, evidence-based protocols rather than relying on its internal, potentially hallucinated parametric memory.

## 🗂️ Document Types

The corpus primarily ingests PDF and Markdown text blobs categorized by source authority:

1. **WHO IMCI Guidelines**: The Integrated Management of Childhood Illness chart booklets. Transcribed into Markdown for cleaner semantic chunking.
2. **NLEM India**: National List of Essential Medicines. Used to verify that generated action plans only prescribe medications available at the ASHA/PHC level.
3. **MoHFW Standard Treatment Guidelines**: Protocols for adult care, maternal health, and endemic infectious diseases (e.g., Dengue, Malaria, Tuberculosis).

## ⚙️ Ingestion Pipeline

```mermaid
graph TD
    RawDocs[Raw PDFs / MDs<br/>(/data/corpus)]:::raw
    
    subgraph RAG Builder (/backend/rag/)
        Splitter[Recursive Character<br/>Text Splitter]:::split
        Embed[MiniLM-L6-v2<br/>Embeddings]:::embed
    end
    
    FAISS[(FAISS Index<br/>.pkl / .faiss)]:::db
    
    RawDocs --> Splitter
    Splitter --> Embed
    Embed --> FAISS
    
    classDef raw fill:#e8eaf6,stroke:#3f51b5
    classDef split fill:#f3e5f5,stroke:#7b1fa2
    classDef embed fill:#e3f2fd,stroke:#1565c0
    classDef db fill:#fff3e0,stroke:#e65100
```

## 📝 Corpus Formatting Rules

To ensure high retrieval accuracy:
- Remove header/footer page numbers before placing text in this folder.
- Use explicit Markdown headers (e.g., `## Classification of Dehydration`) so the LangChain splitters can maintain semantic boundaries during chunking.
- Add metadata YAML frontmatter to documents to aid in source citation (e.g., `source: WHO_IMCI_2014_pg23`).
