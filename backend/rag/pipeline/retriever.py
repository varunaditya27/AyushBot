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

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
from rank_bm25 import BM25Okapi


@dataclass
class RetrievedChunk:
	text: str
	metadata: Dict[str, Any]
	dense_score: float
	sparse_score: float
	fused_score: float


class HybridRetriever:
	def __init__(
		self,
		index: faiss.Index,
		metadata: List[Dict[str, Any]],
		embedder,
		bm25: Optional[BM25Okapi] = None,
	) -> None:
		self._index = index
		self._metadata = metadata
		self._embedder = embedder
		self._bm25 = bm25

	@classmethod
	def from_files(cls, index_path: str, metadata_path: str, embedder) -> "HybridRetriever":
		index = faiss.read_index(index_path)
		with open(metadata_path, "r", encoding="utf-8") as handle:
			metadata = json.load(handle)
		texts = [item.get("text", "") for item in metadata]
		bm25 = BM25Okapi([t.split() for t in texts]) if texts else None
		return cls(index=index, metadata=metadata, embedder=embedder, bm25=bm25)

	def _dense(self, query: str, top_k: int) -> List[Tuple[int, float]]:
		vector = self._embedder.embed(query)
		vector = np.expand_dims(vector, axis=0).astype(np.float32)
		scores, indices = self._index.search(vector, top_k)
		return [(int(idx), float(score)) for idx, score in zip(indices[0], scores[0])]

	def _sparse(self, query: str, top_k: int) -> List[Tuple[int, float]]:
		if not self._bm25:
			return []
		scores = self._bm25.get_scores(query.split())
		ranked = np.argsort(scores)[::-1][:top_k]
		return [(int(idx), float(scores[idx])) for idx in ranked]

	def _rrf(self, dense: List[Tuple[int, float]], sparse: List[Tuple[int, float]], k: int = 60) -> Dict[int, float]:
		scores: Dict[int, float] = {}
		for rank, (idx, _) in enumerate(dense):
			scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
		for rank, (idx, _) in enumerate(sparse):
			scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + rank + 1)
		return scores

	def query(self, query: str, top_k: int = 20, dense_k: int = 100, sparse_k: int = 100) -> List[RetrievedChunk]:
		dense = self._dense(query, dense_k)
		sparse = self._sparse(query, sparse_k)
		fused_scores = self._rrf(dense, sparse)
		ranked = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
		dense_map = {idx: score for idx, score in dense}
		sparse_map = {idx: score for idx, score in sparse}
		results: List[RetrievedChunk] = []
		for idx, fused_score in ranked:
			if idx < 0 or idx >= len(self._metadata):
				continue
			meta = self._metadata[idx]
			results.append(
				RetrievedChunk(
					text=meta.get("text", ""),
					metadata={k: v for k, v in meta.items() if k != "text"},
					dense_score=dense_map.get(idx, 0.0),
					sparse_score=sparse_map.get(idx, 0.0),
					fused_score=float(fused_score),
				)
			)
		return results
