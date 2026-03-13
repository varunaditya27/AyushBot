# =============================================================================
# AyushBot Backend — RAG Pipeline Stage 5: Cross-Encoder Reranker
# =============================================================================
#
# PURPOSE:
#   Performs fine-grained relevance scoring on the top-N retrieved chunks
#   using a cross-encoder model. This is the precision stage that lifts the
#   most clinically relevant chunks to the top before they're fed to the LLM.
#
# WHY A CROSS-ENCODER:
#   Bi-encoders (Stage 2) are fast because query and document are embedded
#   independently — but this independence limits their accuracy for nuanced
#   relevance judgments.
#
#   Cross-encoders take the (query, document) pair as a SINGLE input and
#   output a direct relevance score. This cross-attention mechanism captures
#   fine-grained interactions between query terms and document terms that
#   bi-encoders miss.
#
#   Example: Query "child with cough and high fever"
#     - Bi-encoder might rank "Cough in adults" highly (word overlap)
#     - Cross-encoder correctly ranks "Pediatric pneumonia protocol" higher
#       because it models the interaction between "child" and "pediatric"
#
# MODEL:
#   - ms-marco-MiniLM-L-6-v2 (cross-encoder from sentence-transformers)
#   - ~22M parameters, ~80 MB disk
#   - Takes (query, chunk_text) pair → outputs a relevance score [0.0, 1.0]
#   - More expensive than bi-encoder (~5 ms per pair on RPi 4)
#     → This is why reranking only runs on the top-20 fused results, not
#       the entire corpus
#
# PROCESSING:
#   1. Receive top-N chunks from the retriever's RRF fusion (default: N=20)
#   2. For each chunk, compute cross-encoder score with the query:
#      score = cross_encoder.predict([(query, chunk.text)])
#   3. Sort chunks by cross-encoder score descending
#   4. Return the top-K reranked chunks (default: K=5)
#   5. These 5 chunks become the evidence set for Agent 2's LLM synthesis
#
# MINIMUM RELEVANCE THRESHOLD:
#   If all top-K chunks score below a configurable minimum threshold
#   (default: 0.3), the reranker returns an empty list. This signals to
#   Agent 2 that no relevant clinical protocol was found — triggering the
#   "Unknown presentation — refer to PHC Medical Officer" fallback.
#   This prevents the LLM from synthesizing a response from irrelevant chunks.
#
# INPUTS:
#   - query_text: str
#   - candidate_chunks: list of RetrievedChunk objects (top-20 from retriever)
#   - top_k: int (number to return after reranking, default: 5)
#   - min_score: float (minimum relevance threshold, default: 0.3)
#
# OUTPUTS:
#   - List of RankedChunk objects (top-K), each containing:
#     - All fields from RetrievedChunk
#     - rerank_score: float (cross-encoder relevance score)
#   - Or empty list if no chunk exceeds min_score threshold
#
# CACHING:
#   Cross-encoder model loaded once at startup. Inference is stateless and
#   thread-safe for concurrent requests.
#
# LATENCY TARGET: ~50-100 ms for 20 pairs (on RPi 4)
# =============================================================================
