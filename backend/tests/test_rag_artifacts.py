from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np

from backend.config import clear_settings_cache
from backend.rag import build_index
from backend.rag import retriever as runtime_retriever
from backend.rag.pipeline import indexer


def test_build_chunk_records_include_source_and_embedding_metadata(tmp_path):
	document = tmp_path / "guideline.txt"
	document.write_text(
		"Fever protocol. Hydration advice. " * 20,
		encoding="utf-8",
	)

	records = build_index.build_chunk_records(
		[document],
		chunk_size=80,
		chunk_overlap=0,
		embedding_model_id="synthetic-embedder",
		embedding_model_path=tmp_path / "model",
	)

	assert records
	record = records[0]
	assert record["chunk_id"] == "guideline:0"
	assert record["source"] == "guideline.txt"
	assert record["source_file"] == str(document)
	assert len(record["source_checksum_sha256"]) == 64
	assert record["source_version"] == record["source_checksum_sha256"][:12]
	assert record["embedding_model_id"] == "synthetic-embedder"


def test_validate_inputs_reports_missing_corpus(tmp_path):
	try:
		build_index.validate_inputs(tmp_path / "missing-corpus", tmp_path / "model")
	except SystemExit as exc:
		assert "No cleaned text corpus found" in str(exc)
	else:
		raise AssertionError("Expected missing corpus to stop index build")


def test_build_faiss_index_uses_configurable_hnsw_parameters(monkeypatch):
	created = {}

	class _FakeHnsw:
		efConstruction = None
		efSearch = None

	class _FakeIndex:
		def __init__(self, dim, hnsw_m):
			created["dim"] = dim
			created["hnsw_m"] = hnsw_m
			self.hnsw = _FakeHnsw()
			created["index"] = self

		def add(self, embeddings):
			created["added_shape"] = embeddings.shape

	def _normalize(values):
		created["normalized"] = values.shape

	monkeypatch.setattr(
		indexer,
		"faiss",
		SimpleNamespace(IndexHNSWFlat=_FakeIndex, normalize_L2=_normalize),
	)

	index = indexer.build_faiss_index(
		np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
		use_hnsw=True,
		hnsw_m=12,
		ef_construction=77,
		ef_search=33,
	)

	assert index is created["index"]
	assert created["dim"] == 2
	assert created["hnsw_m"] == 12
	assert index.hnsw.efConstruction == 77
	assert index.hnsw.efSearch == 33
	assert created["added_shape"] == (2, 2)


def test_create_retriever_returns_disabled_when_config_disabled(tmp_path, monkeypatch):
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
rag:
  enabled: false
  index_dir: {tmp_path / "index"}
  model_dir: {tmp_path / "model"}
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()

	retriever = runtime_retriever.create_retriever()
	result = retriever.query("fever")

	assert result["disabled"] is True
	assert result["guardrail_triggered"] is True
	assert result["reason"] == "RAG is disabled in configuration"
	clear_settings_cache()


def test_create_retriever_returns_disabled_when_artifacts_missing(
	tmp_path, monkeypatch
):
	index_dir = tmp_path / "index"
	model_dir = tmp_path / "model"
	index_dir.mkdir()
	model_dir.mkdir()
	config = tmp_path / "config.yaml"
	config.write_text(
		f"""
rag:
  enabled: true
  index_dir: {index_dir}
  model_dir: {model_dir}
""",
		encoding="utf-8",
	)
	monkeypatch.setenv("AYUSHBOT_CONFIG", str(config))
	clear_settings_cache()

	retriever = runtime_retriever.create_retriever()
	result = retriever.query("fever")

	assert result["disabled"] is True
	assert "FAISS index not found" in result["reason"]
	clear_settings_cache()


def test_runtime_metadata_loader_accepts_json_metadata(tmp_path):
	metadata = tmp_path / "metadata.json"
	metadata.write_text(
		json.dumps(
			[
				{
					"text": "synthetic chunk",
					"chunk_id": "synthetic:0",
					"source_checksum_sha256": "a" * 64,
				}
			]
		),
		encoding="utf-8",
	)

	records = runtime_retriever._load_metadata(str(tmp_path))

	assert records[0]["chunk_id"] == "synthetic:0"
