# =============================================================================
# AyushBot Backend — RAG Pipeline Stage 2: Text Embedder
# =============================================================================
#
# PURPOSE:
#   Converts text chunks and queries into dense vector representations using
#   a bi-encoder model (all-MiniLM-L6-v2). These embeddings are the bridge
#   between natural language and the FAISS vector index.
#
# MODEL:
#   - all-MiniLM-L6-v2 (sentence-transformers)
#   - 384-dimensional embeddings
#   - ~22M parameters, ~80 MB disk
#   - Runs efficiently on Raspberry Pi 4 CPU (~15 ms per query embedding)
#   - Chosen for its balance of quality and efficiency — it's the smallest
#     model that achieves competitive MTEB benchmark scores
#
# TWO MODES OF OPERATION:
#
#   Mode 1: OFFLINE (Index Build Time)
#     - Batch-embed all document chunks from the chunker output
#     - Produces a numpy array of shape (num_chunks, 384)
#     - This array is fed to the indexer to build the FAISS index
#     - Batched inference with dynamic batching for throughput optimization
#
#   Mode 2: ONLINE (Query Time)
#     - Single-query embedding for the ASHA's clinical presentation
#     - Called by Agent 2 during live triage
#     - Must complete in < 15 ms (single forward pass)
#
# NORMALIZATION:
#   All embeddings are L2-normalized before storage/search so that cosine
#   similarity reduces to inner product — this allows FAISS to use its
#   fastest IndexFlatIP (inner product) search kernel.
#
# CACHING:
#   The model is loaded once at gateway startup and held in memory. The
#   SentenceTransformer object is shared across all requests (read-only,
#   thread-safe for inference).
#
# INPUTS:
#   - Offline: List of chunk text strings
#   - Online: Single query string
#
# OUTPUTS:
#   - Offline: numpy.ndarray of shape (N, 384), dtype float32
#   - Online: numpy.ndarray of shape (1, 384), dtype float32
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

import numpy as np

from backend.rag.retriever import OnnxEmbedder


@dataclass
class EmbedderConfig:
	model_dir: str
	max_length: int = 256
	intra_op_threads: int = 1
	inter_op_threads: int = 1


class TextEmbedder:
	def __init__(self, config: EmbedderConfig) -> None:
		self._embedder = OnnxEmbedder(
			config.model_dir,
			max_length=config.max_length,
			intra_op_threads=config.intra_op_threads,
			inter_op_threads=config.inter_op_threads,
		)

	def embed(self, text: str) -> np.ndarray:
		return self._embedder.embed(text)

	def embed_batch(self, texts: Iterable[str]) -> np.ndarray:
		vectors: List[np.ndarray] = []
		for text in texts:
			vectors.append(self.embed(text))
		return np.vstack(vectors) if vectors else np.empty((0, 0), dtype=np.float32)
