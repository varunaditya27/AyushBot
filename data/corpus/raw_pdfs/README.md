This directory stores raw PDF source documents for the RAG knowledge base.

CONTENTS:
  National Health Mission (NHM) ASHA worker guideline manuals:
  - ASHA Module 6 & 7: Skills for managing childhood illnesses
  - IMNCI (Integrated Management of Neonatal and Childhood Illness) guidelines
  - National Drug Formulary for primary care
  - WHO Pocket Book of Hospital Care for Children (India adaptation)
  - ASHA facilitator guides and training modules

These PDFs are publicly available from the MoHFW (Ministry of Health and
Family Welfare) and NHM websites. Download them and place them here.

PROCESSING:
  These PDFs are processed by the RAG pipeline:
    1. backend/rag/pipeline/chunker.py — Extracts text, splits into chunks
    2. backend/rag/pipeline/embedder.py — Generates embeddings per chunk
    3. backend/rag/pipeline/indexer.py — Builds the FAISS vector index

OUTPUT: Cleaned text → data/corpus/cleaned_text/
        Chunks → data/corpus/chunks/
        Index → backend/rag/index/

DO NOT COMMIT PDFs TO GIT — they are large binary files.
