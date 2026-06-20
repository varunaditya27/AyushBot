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

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from backend.config import get_settings
from backend.rag.pipeline.chunker import chunk_text


def _parser() -> argparse.ArgumentParser:
	settings = get_settings().rag
	parser = argparse.ArgumentParser(description="Build the local AyushBot RAG index")
	parser.add_argument("--corpus-dir", type=Path, default=settings.corpus_dir)
	parser.add_argument("--output-dir", type=Path, default=settings.index_dir)
	parser.add_argument("--model-dir", type=Path, default=settings.model_dir)
	parser.add_argument("--chunk-size", type=int, default=settings.chunk_size)
	parser.add_argument("--chunk-overlap", type=int, default=settings.chunk_overlap)
	parser.add_argument("--embedding-model-id", default=settings.embedding_model_id)
	parser.add_argument("--use-hnsw", action=argparse.BooleanOptionalAction, default=settings.faiss_use_hnsw)
	parser.add_argument("--hnsw-m", type=int, default=settings.faiss_hnsw_m)
	parser.add_argument("--ef-construction", type=int, default=settings.faiss_ef_construction)
	parser.add_argument("--ef-search", type=int, default=settings.faiss_ef_search)
	return parser


def discover_documents(corpus_dir: Path) -> list[Path]:
	return sorted(corpus_dir.glob("*.txt")) if corpus_dir.is_dir() else []


def _file_sha256(path: Path) -> str:
	digest = hashlib.sha256()
	with path.open("rb") as source:
		for chunk in iter(lambda: source.read(1024 * 1024), b""):
			digest.update(chunk)
	return digest.hexdigest()


def validate_inputs(corpus_dir: Path, model_dir: Path) -> list[Path]:
	documents = sorted(corpus_dir.glob("*.txt")) if corpus_dir.is_dir() else []
	if not documents:
		raise SystemExit(
			f"No cleaned text corpus found in {corpus_dir}. "
			"Add approved .txt guideline files there before building the index."
		)
	for required in ("model.onnx", "tokenizer.json"):
		if not (model_dir / required).is_file():
			raise SystemExit(
				f"Missing local RAG artifact: {model_dir / required}. "
				"Provide an approved ONNX encoder and tokenizer; this command never downloads models."
			)
	return documents


def build_chunk_records(
	documents: list[Path],
	*,
	chunk_size: int,
	chunk_overlap: int,
	embedding_model_id: str,
	embedding_model_path: Path,
) -> list[dict[str, Any]]:
	records: list[dict[str, Any]] = []
	for document in documents:
		checksum = _file_sha256(document)
		for index, chunk in enumerate(
			chunk_text(
				document.read_text(encoding="utf-8"),
				max_tokens=chunk_size,
				overlap=chunk_overlap,
			)
		):
			records.append(
				{
					"id": f"{document.stem}:{index}",
					"chunk_id": f"{document.stem}:{index}",
					"source": document.name,
					"source_file": str(document),
					"source_checksum_sha256": checksum,
					"source_version": checksum[:12],
					"embedding_model_id": embedding_model_id,
					"embedding_model_path": str(embedding_model_path),
					"text": chunk.text,
					"token_count": chunk.token_count,
				}
			)
	return records


def main() -> int:
	args = _parser().parse_args()
	documents = validate_inputs(args.corpus_dir, args.model_dir)

	try:
		from backend.rag.pipeline.embedder import EmbedderConfig, TextEmbedder
		from backend.rag.pipeline.indexer import build_faiss_index, save_index, save_metadata
	except ImportError as exc:
		raise SystemExit(
			"RAG build dependencies are missing. Install the project AI dependencies first."
		) from exc

	records = build_chunk_records(
		documents,
		chunk_size=args.chunk_size,
		chunk_overlap=args.chunk_overlap,
		embedding_model_id=args.embedding_model_id,
		embedding_model_path=args.model_dir,
	)

	embedder = TextEmbedder(EmbedderConfig(model_dir=str(args.model_dir)))
	embeddings = np.vstack([embedder.embed(str(record["text"])) for record in records])
	index = build_faiss_index(
		embeddings,
		use_hnsw=args.use_hnsw,
		hnsw_m=args.hnsw_m,
		ef_construction=args.ef_construction,
		ef_search=args.ef_search,
	)

	args.output_dir.mkdir(parents=True, exist_ok=True)
	save_index(index, str(args.output_dir / "faiss.index"))
	save_metadata(records, str(args.output_dir / "metadata.json"))
	manifest = {
		"built_at": datetime.now(timezone.utc).isoformat(),
		"documents": len(documents),
		"chunks": len(records),
		"embedding_model_id": args.embedding_model_id,
		"embedding_model_path": str(args.model_dir),
		"index_type": "HNSW" if args.use_hnsw else "FlatIP",
		"faiss": {
			"use_hnsw": args.use_hnsw,
			"hnsw_m": args.hnsw_m,
			"ef_construction": args.ef_construction,
			"ef_search": args.ef_search,
		},
	}
	(args.output_dir / "manifest.json").write_text(
		json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
	)
	print(f"Built {len(records)} chunks from {len(documents)} documents in {args.output_dir}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
