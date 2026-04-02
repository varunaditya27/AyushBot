# =============================================================================
# AyushBot Tests — Unit: RAG Retrieval Pipeline
# =============================================================================
#
# PURPOSE:
#   Unit tests for each stage of the RAG (Retrieval-Augmented Generation)
#   pipeline defined in backend/rag/pipeline/.
#
# TEST CASES:
#
#   --- Chunker (pipeline/chunker.py) ---
#
#   test_chunker_respects_max_tokens
#     Input: A long text string (5000 tokens)
#     Expected: Each chunk is <= 512 tokens (configured chunk size)
#
#   test_chunker_preserves_sentence_boundaries
#     Input: Text with clear sentence boundaries
#     Expected: Chunks do not split mid-sentence (semantic coherence)
#
#   test_chunker_overlap
#     Input: Text requiring multiple chunks
#     Expected: Adjacent chunks overlap by ~50 tokens (configured overlap)
#
#   --- Embedder (pipeline/embedder.py) ---
#
#   test_embedder_output_dimension
#     Input: A single text chunk
#     Expected: Embedding vector has dimension 384 (all-MiniLM-L6-v2 output)
#
#   test_embedder_similar_texts_close
#     Input: Two semantically similar chunks (about fever treatment)
#     Expected: Cosine similarity > 0.7
#
#   test_embedder_dissimilar_texts_far
#     Input: Two unrelated chunks (fever treatment vs. vaccination schedule)
#     Expected: Cosine similarity < 0.4
#
#   --- Retriever (pipeline/retriever.py) ---
#
#   test_retriever_returns_top_k
#     Input: Query, k=5
#     Expected: Exactly 5 chunks returned, ordered by relevance score
#
#   test_retriever_relevant_chunks_ranked_higher
#     Input: Query "child has high fever and cough"
#     Index: Contains chunks about pneumonia, vaccination, nutrition, fever
#     Expected: Fever and pneumonia chunks ranked in top 2
#
#   --- Reranker (pipeline/reranker.py) ---
#
#   test_reranker_improves_ranking
#     Input: Top-10 retriever results (some irrelevant results in top 5)
#     Expected: After reranking, the top-3 are more clinically relevant
#       than the retriever's top-3 (measured by a reference ranking)
#
#   test_reranker_prunes_irrelevant
#     Input: Top-10 results, relevance threshold = 0.3
#     Expected: Chunks with reranker score < 0.3 are dropped
#
# FIXTURES USED:
#   - mock_faiss_index (small pre-built test index)
# =============================================================================

import pytest

pytest.importorskip("faiss")

import pytest

pytest.importorskip("faiss")
pytest.importorskip("rank_bm25")

import numpy as np

from backend.rag.pipeline.chunker import chunk_text
from backend.rag.pipeline.indexer import build_faiss_index
from backend.rag.pipeline.retriever import HybridRetriever


class _DummyEmbedder:
	def embed(self, text: str) -> np.ndarray:
		if "fever" in text:
			return np.array([1.0, 0.0, 0.0], dtype=np.float32)
		if "cough" in text:
			return np.array([0.0, 1.0, 0.0], dtype=np.float32)
		return np.array([0.0, 0.0, 1.0], dtype=np.float32)


def test_chunker_respects_max_tokens():
	text = "Sentence. " * 200
	chunks = chunk_text(text, max_tokens=50, overlap=10)
	assert all(chunk.token_count <= 50 for chunk in chunks)


def test_retriever_returns_top_k():
	embeddings = np.array(
		[
			[1.0, 0.0, 0.0],
			[0.0, 1.0, 0.0],
			[0.0, 0.0, 1.0],
		],
		dtype=np.float32,
	)
	index = build_faiss_index(embeddings, use_hnsw=False)
	metadata = [
		{"text": "fever protocol"},
		{"text": "cough protocol"},
		{"text": "nutrition"},
	]
	retriever = HybridRetriever(index=index, metadata=metadata, embedder=_DummyEmbedder())
	results = retriever.query("fever", top_k=2, dense_k=2, sparse_k=0)
	assert len(results) == 2
	assert results[0].text == "fever protocol"
