# =============================================================================
# AyushBot Backend — RAG (Retrieval-Augmented Generation) Package
# =============================================================================
#
# This package implements the EdgeRAG pipeline — the retrieval engine that
# Agent 2 (Differential Diagnosis) uses to find evidence-backed clinical
# protocol chunks before any LLM synthesis occurs.
#
# The pipeline is split into two phases:
#   1. OFFLINE (build-time): Ingest PDFs → chunk → embed → build FAISS index
#   2. ONLINE (query-time): Embed query → retrieve → rerank → return top-K
#
# Subpackages:
#   - pipeline/: The five-stage online retrieval pipeline components
#   - build_index.py: The offline index construction entry point
#   - index/: Directory for the serialized FAISS index files
# =============================================================================
