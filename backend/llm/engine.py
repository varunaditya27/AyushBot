"""AyushBot Backend — llama.cpp inference engine with GBNF grammar support."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Type

import yaml
from llama_cpp import Llama
from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class LlmConfig:
    model_path: str
    context_length: int
    max_tokens: int
    temperature: float
    top_p: float
    n_threads: int
    n_gpu_layers: int


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


def _build_config(config_path: Optional[str] = None) -> LlmConfig:
    config = _load_config(config_path)
    llm_cfg = config.get("llm", {}) if isinstance(config, dict) else {}
    model_path = os.getenv("AYUSHBOT_LLM_MODEL_PATH", llm_cfg.get("model_path", ""))
    if not model_path:
        raise ValueError("LLM model_path must be configured")

    context_length = int(os.getenv("AYUSHBOT_LLM_CONTEXT", llm_cfg.get("context_length", 2048)))
    max_tokens = int(os.getenv("AYUSHBOT_LLM_MAX_TOKENS", llm_cfg.get("max_tokens", 300)))
    temperature = float(os.getenv("AYUSHBOT_LLM_TEMPERATURE", llm_cfg.get("temperature", 0.1)))
    top_p = float(os.getenv("AYUSHBOT_LLM_TOP_P", llm_cfg.get("top_p", 0.9)))
    n_threads = int(os.getenv("AYUSHBOT_LLM_THREADS", llm_cfg.get("n_threads", 2)))
    n_gpu_layers = int(os.getenv("AYUSHBOT_LLM_GPU_LAYERS", llm_cfg.get("n_gpu_layers", 0)))
    context_length = min(context_length, 2048)

    return LlmConfig(
        model_path=model_path,
        context_length=context_length,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n_threads=n_threads,
        n_gpu_layers=n_gpu_layers,
    )


class _GrammarBuilder:
    def __init__(self) -> None:
        self._rules: Dict[str, str] = {}
        self._counter = 0
        self._ensure_base_rules()

    def _ensure_base_rules(self) -> None:
        self._rules["ws"] = r"[ \t\n\r]*"
        self._rules["number"] = r"-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?"
        self._rules["bool"] = r"true|false"
        self._rules["null"] = r"null"
        self._rules["hex"] = r"[0-9a-fA-F]"
        self._rules["escape"] = '"\\\\" (["\\\\/bfnrt] | "u" hex hex hex hex)'
        self._rules["char"] = r"[^\\\"\n\r]"
        self._rules["string"] = '"\\\"" (char | escape)* "\\\""'

    def _next_rule(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}_{self._counter}"

    def _rule_for_schema(self, schema: Dict[str, Any]) -> str:
        schema_type = schema.get("type")
        if schema_type == "string":
            return "string"
        if schema_type == "integer" or schema_type == "number":
            return "number"
        if schema_type == "boolean":
            return "bool"
        if schema_type == "array":
            return self._array_rule(schema)
        if schema_type == "object" or "properties" in schema:
            return self._object_rule(schema)
        if "anyOf" in schema:
            return self._union_rule(schema["anyOf"])
        return "string"

    def _union_rule(self, options: Any) -> str:
        union_rule = self._next_rule("union")
        parts = [self._rule_for_schema(opt) for opt in options if isinstance(opt, dict)]
        if not parts:
            self._rules[union_rule] = "string"
        else:
            self._rules[union_rule] = " | ".join(parts)
        return union_rule

    def _array_rule(self, schema: Dict[str, Any]) -> str:
        items = schema.get("items", {}) if isinstance(schema, dict) else {}
        item_rule = self._rule_for_schema(items) if items else "string"
        array_rule = self._next_rule("array")
        self._rules[array_rule] = (
            f'"[" ws {item_rule} (ws "," ws {item_rule})* ws "]" | "[" ws "]"'
        )
        return array_rule

    def _object_rule(self, schema: Dict[str, Any]) -> str:
        props = schema.get("properties", {}) if isinstance(schema, dict) else {}
        required = schema.get("required", list(props.keys()))
        keys = list(required) + [key for key in props.keys() if key not in required]
        object_rule = self._next_rule("object")
        if not keys:
            self._rules[object_rule] = '"{" ws "}"'
            return object_rule

        members = []
        for key in keys:
            value_schema = props.get(key, {"type": "string"})
            value_rule = self._rule_for_schema(value_schema)
            members.append(f'"{key}" ws ":" ws {value_rule}')

        joined = ' ws "," ws '.join(members)
        self._rules[object_rule] = f'"{{" ws {joined} ws "}}"'
        return object_rule

    def build(self, schema: Dict[str, Any]) -> str:
        root_rule = self._rule_for_schema(schema)
        self._rules["root"] = root_rule
        lines = []
        for name, rule in self._rules.items():
            lines.append(f"{name} ::= {rule}")
        return "\n".join(lines)


def build_gbnf_from_model(model: Type[BaseModel]) -> str:
    schema = model.model_json_schema()
    builder = _GrammarBuilder()
    return builder.build(schema)


class LlamaEngine:
    def __init__(self, config: Optional[LlmConfig] = None) -> None:
        self.config = config or _build_config()
        self._model = self._load_model(self.config)

    @staticmethod
    def _load_model(config: LlmConfig) -> Llama:
        if not os.path.exists(config.model_path):
            raise FileNotFoundError(f"Model file not found: {config.model_path}")
        try:
            return Llama(
                model_path=config.model_path,
                n_ctx=config.context_length,
                n_threads=config.n_threads,
                n_gpu_layers=config.n_gpu_layers,
                logits_all=False,
                verbose=False,
            )
        except Exception as exc:
            raise RuntimeError(f"Failed to load GGUF model: {exc}") from exc

    def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        grammar: Optional[str] = None,
        stop: Optional[Tuple[str, ...]] = None,
    ) -> str:
        try:
            output = self._model(
                prompt,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature if temperature is not None else self.config.temperature,
                top_p=top_p if top_p is not None else self.config.top_p,
                stop=list(stop) if stop else None,
                grammar=grammar,
            )
            return output["choices"][0]["text"]
        except Exception as exc:
            raise RuntimeError(f"LLM inference failed: {exc}") from exc

    def generate_json(
        self,
        prompt: str,
        schema_model: Type[BaseModel],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        stop: Optional[Tuple[str, ...]] = None,
    ) -> str:
        grammar = build_gbnf_from_model(schema_model)
        return self.generate(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            grammar=grammar,
            stop=stop,
        )


def create_engine(config_path: Optional[str] = None) -> LlamaEngine:
    return LlamaEngine(_build_config(config_path))
