# =============================================================================
# AyushBot Backend — RAG Pipeline Stage 4: Hybrid Retriever
# =============================================================================
#
# PURPOSE:
#   Executes the actual evidence retrieval during live triage. Combines dense
#   (FAISS) and sparse (BM25) retrieval, then fuses results using Reciprocal
#   Rank Fusion (RRF) to maximize both semantic and lexical recall.
#
# WHY HYBRID RETRIEVAL:
#   Dense retrieval (FAISS) is great at capturing semantic meaning
#   ("breathing difficulty" ≈ "respiratory distress") but can miss exact
#   clinical keywords (drug names, ICD codes, specific abbreviations).
#
#   Sparse retrieval (BM25) catches exact keyword matches ("Amoxicillin",
#   "J18.9", "IMNCI") but misses semantically equivalent paraphrases.
#
#   Combining both ensures that no relevant evidence is missed — critical
#   when a missed retrieval could mean a missed diagnosis.
#
# ARCHITECTURE:
#
#   1. Dense Retrieval Path (FAISS)
#      - Load the pre-built FAISS HNSW index at startup (from rag/index/)
#      - Embed the query using the bi-encoder (embedder.py)
#      - Search FAISS for top-K_dense nearest neighbors (default: K=100)
#      - Returns: list of (chunk_id, cosine_similarity_score)
#
#   2. Sparse Retrieval Path (BM25)
#      - Build a BM25 index from all chunk texts at startup (using rank_bm25)
#      - Tokenize the query and score against all chunks
#      - Take top-K_sparse results (default: K=100)
#      - Returns: list of (chunk_id, bm25_score)
#
#   3. Reciprocal Rank Fusion (RRF)
#      - For each chunk appearing in either result set:
#        RRF_score = Σ (1 / (k + rank_in_list)) for each list it appears in
#        where k = 60 (standard RRF constant)
#      - Sort by RRF_score descending
#      - Take top-N fused results (default: N=20)
#      - This balances semantic relevance with keyword precision
#
# STARTUP:
#   On gateway boot, the retriever:
#   1. Loads the FAISS index into memory (~10-50 MB)
#   2. Loads the chunk metadata mapping (JSON)
#   3. Builds the BM25 index from chunk texts (takes ~1-2 seconds)
#   4. All subsequent queries are instant (no disk I/O during live triage)
#
# INPUTS:
#   - query_text: str (from Agent 2's query construction step)
#   - top_k: int (number of fused results to return, default: 20)
#
# OUTPUTS:
#   - List of RetrievedChunk objects, each containing:
#     - chunk_text: str
#     - source_document: str
#     - page_number: int
#     - section_heading: str
#     - dense_score: float (FAISS similarity)
#     - sparse_score: float (BM25 score)
#     - fused_score: float (RRF score)
#
# LATENCY TARGET: < 50 ms for dense + sparse + fusion (on RPi 4)
# =============================================================================
