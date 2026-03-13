# =============================================================================
# AyushBot Backend — RAG Pipeline Package
# =============================================================================
#
# This sub-package contains the five modular stages of the EdgeRAG retrieval
# pipeline. Each stage is a standalone module that can be tested, profiled,
# and swapped independently.
#
# Pipeline flow:
#   Query → Chunker (offline) → Embedder → Indexer/Retriever → Reranker → Top-K
# =============================================================================
