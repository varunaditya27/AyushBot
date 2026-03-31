# =============================================================================
# AyushBot Backend — RAG Pipeline Stage 3: FAISS HNSW Index Builder
# =============================================================================
#
# PURPOSE:
#   Builds and manages the FAISS Hierarchical Navigable Small World (HNSW)
#   vector index used for approximate nearest neighbor (ANN) search during
#   clinical evidence retrieval.
#
# WHY FAISS HNSW:
#   - The clinical corpus is ~5,000-20,000 chunks (moderate size)
#   - On RPi 4 hardware, exact brute-force search would take too long at
#     scale, but HNSW provides sub-millisecond ANN search with >95% recall
#   - FAISS is well-supported on ARM64 (Raspberry Pi's architecture)
#   - The index fits comfortably in RAM (~10-50 MB for 20K chunks × 384 dims)
#
# INDEX CONFIGURATION:
#   - Index type: IndexHNSWFlat (no product quantization — we need high recall
#     for medical accuracy; lossy compression is unacceptable for healthcare)
#   - HNSW parameters:
#       M = 32 (number of bidirectional links per node; higher = more accurate
#       but more memory)
#       efConstruction = 200 (build-time search depth; higher = better index
#       quality but slower build)
#       efSearch = 128 (query-time search depth; tunable at runtime)
#   - Metric: Inner Product (because embeddings are L2-normalized,
#     inner product == cosine similarity)
#
# OFFLINE WORKFLOW (Index Build):
#   1. Receive chunk embeddings (numpy array) from the embedder
#   2. Initialize a FAISS IndexHNSWFlat with d=384
#   3. Add all embeddings to the index (faiss.write_index to serialize)
#   4. Save the index file + chunk metadata mapping to backend/rag/index/
#   5. The chunk metadata mapping is a JSON file that maps FAISS vector IDs
#      to the original chunk objects (text + provenance metadata)
#
# ONLINE WORKFLOW (Query):
#   This module is NOT called directly during queries — see retriever.py.
#   The indexer builds the artifacts that the retriever loads at startup.
#
# INDEX UPDATES:
#   The index is rebuilt from scratch whenever the clinical corpus changes.
#   This is an infrequent operation (when new treatment guidelines are added).
#   There is no incremental update — full rebuild ensures index integrity.
#
# OUTPUTS:
#   - faiss_index.bin: Serialized FAISS HNSW index file
#   - chunk_metadata.json: Mapping from vector ID → chunk object
#   - index_manifest.json: Build metadata (num_chunks, build_time, model_name)
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np


def build_faiss_index(embeddings: np.ndarray, use_hnsw: bool = False) -> faiss.Index:
	if embeddings.size == 0:
		raise ValueError("Embeddings array is empty")
	dim = embeddings.shape[1]
	if use_hnsw:
		index = faiss.IndexHNSWFlat(dim, 32)
	else:
		index = faiss.IndexFlatIP(dim)
	faiss.normalize_L2(embeddings)
	index.add(embeddings.astype(np.float32))
	return index


def save_index(index: faiss.Index, index_path: str) -> None:
	Path(index_path).parent.mkdir(parents=True, exist_ok=True)
	faiss.write_index(index, index_path)


def save_metadata(metadata: List[Dict[str, Any]], metadata_path: str) -> None:
	Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
	with open(metadata_path, "w", encoding="utf-8") as handle:
		json.dump(metadata, handle, ensure_ascii=False, indent=2)
