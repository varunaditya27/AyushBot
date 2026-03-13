# =============================================================================
# AyushBot Backend — RAG Offline Index Builder (CLI Entry Point)
# =============================================================================
#
# PURPOSE:
#   Command-line script that orchestrates the offline RAG index construction
#   pipeline. Run this BEFORE deploying to the gateway — it ingests the
#   clinical corpus and produces the FAISS index + metadata files that the
#   retriever loads at runtime.
#
# THIS SCRIPT IS NOT PART OF THE LIVE TRIAGE PIPELINE.
#   It runs once (or whenever the clinical corpus changes) on a development
#   machine or CI server. The output artifacts are then deployed to the
#   gateway's backend/rag/index/ directory.
#
# PIPELINE STEPS:
#
#   Step 1 — Corpus Discovery
#     Scan data/corpus/cleaned_text/ for all .txt files.
#     Each file corresponds to one clinical guideline or treatment protocol.
#     Log the total number of documents found.
#
#   Step 2 — Chunking
#     Run pipeline/chunker.py on each document:
#       - Apply section-boundary splitting + sliding-window sub-chunking
#       - Tag each chunk with provenance metadata
#     Log the total number of chunks produced.
#
#   Step 3 — Embedding
#     Run pipeline/embedder.py in batch mode:
#       - Embed all chunks using all-MiniLM-L6-v2
#       - Produce a numpy array of shape (num_chunks, 384)
#     Log the embedding time and throughput (chunks/sec).
#
#   Step 4 — Indexing
#     Run pipeline/indexer.py:
#       - Build the FAISS HNSW index from the embedding matrix
#       - Serialize the index to backend/rag/index/faiss_index.bin
#       - Write the chunk metadata mapping to backend/rag/index/chunk_metadata.json
#       - Write the build manifest to backend/rag/index/index_manifest.json
#     Log the index build time, file size, and HNSW parameters used.
#
#   Step 5 — Validation (Optional but Recommended)
#     Run a small set of smoke-test queries against the newly built index
#     to verify that retrieval is working:
#       - "child with severe pneumonia treatment protocol"
#       - "ORS dosage for diarrhea in infants"
#       - "danger signs for neonatal sepsis"
#     Log the top-3 retrieved chunk titles for each smoke-test query.
#     If no relevant chunks are found, emit a WARNING.
#
# CLI USAGE:
#   python -m backend.rag.build_index \
#     --corpus-dir data/corpus/cleaned_text/ \
#     --output-dir backend/rag/index/ \
#     --chunk-size 300 \
#     --chunk-overlap 50 \
#     --validate
#
# CONFIGURATION:
#   All parameters (chunk size, overlap, HNSW M, efConstruction, etc.) are
#   loaded from backend/config.yaml under the "rag" section.
#
# OUTPUTS:
#   - backend/rag/index/faiss_index.bin (~10-50 MB depending on corpus size)
#   - backend/rag/index/chunk_metadata.json (~5-20 MB)
#   - backend/rag/index/index_manifest.json (~1 KB, build metadata)
# =============================================================================
