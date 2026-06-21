"""AyushBot Backend — llama.cpp inference engine with GBNF grammar support."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Type

from pydantic import BaseModel

from backend.config import load_settings

if TYPE_CHECKING:
	from llama_cpp import Llama

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


def _build_config(config_path: Optional[str] = None) -> LlmConfig:
    llm_cfg = load_settings(config_path).llm

    return LlmConfig(
        model_path=str(llm_cfg.model_path),
        context_length=llm_cfg.context_length,
        max_tokens=llm_cfg.max_tokens,
        temperature=llm_cfg.temperature,
        top_p=llm_cfg.top_p,
        n_threads=llm_cfg.n_threads,
        n_gpu_layers=llm_cfg.n_gpu_layers,
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
    def _load_model(config: LlmConfig) -> "Llama":
        from pathlib import Path

        if not Path(config.model_path).exists():
            raise FileNotFoundError(f"Model file not found: {config.model_path}")
        try:
            from llama_cpp import Llama

            return Llama(
                model_path=config.model_path,
                n_ctx=config.context_length,
                n_threads=config.n_threads,
                n_gpu_layers=config.n_gpu_layers,
                logits_all=False,
                verbose=False,
            )
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed; install the AI dependencies to use the LLM"
            ) from exc
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
