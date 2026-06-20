"""AyushBot Backend — ONNX + FAISS Retriever."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np

from backend.config import load_settings

if TYPE_CHECKING:
	from tokenizers import Tokenizer

logger = logging.getLogger(__name__)


@dataclass
class RetrieverConfig:
    enabled: bool
    index_dir: str
    model_dir: str
    embedding_model_id: str
    top_k: int
    dense_top_k: int
    min_score: float
    faiss_ef_search: int
    max_length: int
    intra_op_threads: int
    inter_op_threads: int


def _build_config(config_path: Optional[str] = None) -> RetrieverConfig:
    rag_cfg = load_settings(config_path).rag
    return RetrieverConfig(
        enabled=rag_cfg.enabled,
        index_dir=str(rag_cfg.index_dir),
        model_dir=str(rag_cfg.model_dir),
        embedding_model_id=rag_cfg.embedding_model_id,
        top_k=rag_cfg.retriever_top_k_fused,
        dense_top_k=rag_cfg.dense_top_k,
        min_score=rag_cfg.reranker_min_score,
        faiss_ef_search=rag_cfg.faiss_ef_search,
        max_length=rag_cfg.max_length,
        intra_op_threads=rag_cfg.intra_op_threads,
        inter_op_threads=rag_cfg.inter_op_threads,
    )


def _resolve_tokenizer_path(model_dir: str) -> str:
    candidate = Path(model_dir) / "tokenizer.json"
    if not candidate.exists():
        raise FileNotFoundError(f"tokenizer.json not found in {model_dir}")
    return str(candidate)


def _resolve_onnx_path(model_dir: str) -> str:
    candidate = Path(model_dir) / "model.onnx"
    if not candidate.exists():
        raise FileNotFoundError(f"model.onnx not found in {model_dir}")
    return str(candidate)


def _load_metadata(index_dir: str) -> List[Dict[str, Any]]:
    jsonl_path = Path(index_dir) / "metadata.jsonl"
    json_path = Path(index_dir) / "metadata.json"
    if jsonl_path.exists():
        records: List[Dict[str, Any]] = []
        with open(jsonl_path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
        return records
    if json_path.exists():
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
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise RuntimeError(
                "onnxruntime and tokenizers are required for model-backed RAG"
            ) from exc
        tokenizer_path = _resolve_tokenizer_path(model_dir)
        onnx_path = _resolve_onnx_path(model_dir)
        self._tokenizer: "Tokenizer" = Tokenizer.from_file(tokenizer_path)
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
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError("faiss-cpu is required for model-backed RAG") from exc
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
        ef_search: int = 128,
    ) -> None:
        index_path = Path(index_dir) / "faiss.index"
        if not index_path.exists():
            raise FileNotFoundError(f"FAISS index not found at {index_path}")
        try:
            import faiss
        except ImportError as exc:
            raise RuntimeError("faiss-cpu is required for model-backed RAG") from exc
        self._index = faiss.read_index(str(index_path))
        if hasattr(self._index, "hnsw"):
            self._index.hnsw.efSearch = ef_search
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


class DisabledRetriever:
    def __init__(self, reason: str) -> None:
        self.reason = reason

    def query(self, _text: str, top_k: Optional[int] = None) -> Dict[str, Any]:
        return {
            "results": [],
            "guardrail_triggered": True,
            "disabled": True,
            "reason": self.reason,
        }


def _missing_artifact_reason(cfg: RetrieverConfig) -> str | None:
    index_dir = Path(cfg.index_dir)
    model_dir = Path(cfg.model_dir)
    if not (index_dir / "faiss.index").is_file():
        return f"FAISS index not found at {index_dir / 'faiss.index'}"
    if not ((index_dir / "metadata.json").is_file() or (index_dir / "metadata.jsonl").is_file()):
        return f"RAG metadata not found in {index_dir}"
    if not (model_dir / "model.onnx").is_file():
        return f"ONNX model not found at {model_dir / 'model.onnx'}"
    if not (model_dir / "tokenizer.json").is_file():
        return f"Tokenizer not found at {model_dir / 'tokenizer.json'}"
    return None


def create_retriever(config_path: Optional[str] = None) -> FaissRetriever | DisabledRetriever:
    cfg = _build_config(config_path)
    if not cfg.enabled:
        return DisabledRetriever("RAG is disabled in configuration")
    missing = _missing_artifact_reason(cfg)
    if missing:
        logger.warning("RAG disabled: %s", missing)
        return DisabledRetriever(missing)
    try:
        embedder = OnnxEmbedder(
            cfg.model_dir,
            max_length=cfg.max_length,
            intra_op_threads=cfg.intra_op_threads,
            inter_op_threads=cfg.inter_op_threads,
        )
        return FaissRetriever(
            cfg.index_dir,
            embedder,
            top_k=cfg.top_k,
            min_score=cfg.min_score,
            ef_search=cfg.faiss_ef_search,
        )
    except Exception as exc:
        logger.warning("RAG disabled: %s", exc)
        return DisabledRetriever(str(exc))
