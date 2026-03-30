"""AyushBot Backend — ONNX + FAISS Retriever."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np
import onnxruntime as ort
import yaml
from tokenizers import Tokenizer

logger = logging.getLogger(__name__)


@dataclass
class RetrieverConfig:
    index_dir: str
    model_dir: str
    top_k: int
    min_score: float
    max_length: int
    intra_op_threads: int
    inter_op_threads: int


def _load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    path = (
        config_path
        or os.getenv("AYUSHBOT_CONFIG")
        or os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    )
    path = os.path.abspath(path)
    if not os.path.exists(path):
        logger.warning("Config file not found at %s; using defaults", path)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to load config: %s", exc)
        return {}


def _build_config(config_path: Optional[str] = None) -> RetrieverConfig:
    config = _load_config(config_path)
    rag_cfg = config.get("rag", {}) if isinstance(config, dict) else {}
    index_dir = os.getenv("AYUSHBOT_RAG_INDEX_DIR", rag_cfg.get("index_dir", "rag/index"))
    model_dir = os.getenv(
        "AYUSHBOT_RAG_MODEL_DIR", rag_cfg.get("biencoder_model", "all-MiniLM-L6-v2")
    )
    top_k = int(os.getenv("AYUSHBOT_RAG_TOP_K", rag_cfg.get("retriever_top_k_fused", 20)))
    min_score = float(
        os.getenv("AYUSHBOT_RAG_MIN_SCORE", rag_cfg.get("reranker_min_score", 0.3))
    )
    max_length = int(os.getenv("AYUSHBOT_RAG_MAX_LENGTH", rag_cfg.get("max_length", 256)))
    intra = int(os.getenv("AYUSHBOT_RAG_INTRA_THREADS", rag_cfg.get("intra_op_threads", 1)))
    inter = int(os.getenv("AYUSHBOT_RAG_INTER_THREADS", rag_cfg.get("inter_op_threads", 1)))
    return RetrieverConfig(
        index_dir=os.path.abspath(index_dir),
        model_dir=os.path.abspath(model_dir),
        top_k=top_k,
        min_score=min_score,
        max_length=max_length,
        intra_op_threads=intra,
        inter_op_threads=inter,
    )


def _resolve_tokenizer_path(model_dir: str) -> str:
    candidate = os.path.join(model_dir, "tokenizer.json")
    if not os.path.exists(candidate):
        raise FileNotFoundError(f"tokenizer.json not found in {model_dir}")
    return candidate


def _resolve_onnx_path(model_dir: str) -> str:
    candidate = os.path.join(model_dir, "model.onnx")
    if not os.path.exists(candidate):
        raise FileNotFoundError(f"model.onnx not found in {model_dir}")
    return candidate


def _load_metadata(index_dir: str) -> List[Dict[str, Any]]:
    jsonl_path = os.path.join(index_dir, "metadata.jsonl")
    json_path = os.path.join(index_dir, "metadata.json")
    if os.path.exists(jsonl_path):
        records: List[Dict[str, Any]] = []
        with open(jsonl_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return data
    raise FileNotFoundError("metadata.jsonl or metadata.json not found in index dir")


class OnnxEmbedder:
    def __init__(
        self,
        model_dir: str,
        max_length: int = 256,
        intra_op_threads: int = 1,
        inter_op_threads: int = 1,
    ) -> None:
        tokenizer_path = _resolve_tokenizer_path(model_dir)
        onnx_path = _resolve_onnx_path(model_dir)
        self._tokenizer = Tokenizer.from_file(tokenizer_path)
        self.max_length = max_length

        sess_options = ort.SessionOptions()
        sess_options.intra_op_num_threads = max(1, intra_op_threads)
        sess_options.inter_op_num_threads = max(1, inter_op_threads)
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
        self._session = ort.InferenceSession(onnx_path, sess_options, providers=["CPUExecutionProvider"])
        self._input_names = {inp.name for inp in self._session.get_inputs()}

    def _pad_id(self) -> int:
        for token in ("[PAD]", "<pad>"):
            token_id = self._tokenizer.token_to_id(token)
            if token_id is not None:
                return int(token_id)
        return 0

    def _tokenize(self, text: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        encoding = self._tokenizer.encode(text)
        input_ids = encoding.ids
        if self.max_length and len(input_ids) > self.max_length:
            input_ids = input_ids[: self.max_length]
        attention_mask = [1] * len(input_ids)

        if self.max_length:
            pad_len = self.max_length - len(input_ids)
            if pad_len > 0:
                pad_id = self._pad_id()
                input_ids = input_ids + [pad_id] * pad_len
                attention_mask = attention_mask + [0] * pad_len

        token_type_ids = [0] * len(input_ids)
        return (
            np.array([input_ids], dtype=np.int64),
            np.array([attention_mask], dtype=np.int64),
            np.array([token_type_ids], dtype=np.int64),
        )

    def embed(self, text: str) -> np.ndarray:
        input_ids, attention_mask, token_type_ids = self._tokenize(text)
        inputs: Dict[str, np.ndarray] = {}
        if "input_ids" in self._input_names:
            inputs["input_ids"] = input_ids
        if "attention_mask" in self._input_names:
            inputs["attention_mask"] = attention_mask
        if "token_type_ids" in self._input_names:
            inputs["token_type_ids"] = token_type_ids

        outputs = self._session.run(None, inputs)
        last_hidden = outputs[0]
        mask = attention_mask.astype(np.float32)[:, :, None]
        summed = (last_hidden * mask).sum(axis=1)
        counts = np.clip(mask.sum(axis=1), 1e-9, None)
        embedding = summed / counts
        embedding = embedding.astype(np.float32)
        faiss.normalize_L2(embedding)
        return embedding[0]


class FaissRetriever:
    def __init__(
        self,
        index_dir: str,
        embedder: OnnxEmbedder,
        top_k: int = 20,
        min_score: float = 0.3,
    ) -> None:
        index_path = os.path.join(index_dir, "faiss.index")
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        self._index = faiss.read_index(index_path)
        self._metadata = _load_metadata(index_dir)
        self._embedder = embedder
        self._top_k = top_k
        self._min_score = min_score

    def query(self, text: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        embedding = self._embedder.embed(text)
        embedding = np.expand_dims(embedding, axis=0)
        k = top_k or self._top_k
        scores, indices = self._index.search(embedding, k)
        scores = scores[0]
        indices = indices[0]

        results: List[Dict[str, Any]] = []
        max_score = None
        for score, idx in zip(scores, indices):
            if idx < 0 or idx >= len(self._metadata):
                continue
            max_score = score if max_score is None else max(max_score, score)
            if score < self._min_score:
                continue
            metadata = self._metadata[idx]
            results.append(
                {
                    "score": float(score),
                    "text": metadata.get("text"),
                    "metadata": {k: v for k, v in metadata.items() if k != "text"},
                }
            )

        guardrail_triggered = max_score is None or max_score < self._min_score
        return {"results": results, "guardrail_triggered": guardrail_triggered}


def create_retriever(config_path: Optional[str] = None) -> FaissRetriever:
    cfg = _build_config(config_path)
    embedder = OnnxEmbedder(
        cfg.model_dir,
        max_length=cfg.max_length,
        intra_op_threads=cfg.intra_op_threads,
        inter_op_threads=cfg.inter_op_threads,
    )
    return FaissRetriever(cfg.index_dir, embedder, top_k=cfg.top_k, min_score=cfg.min_score)