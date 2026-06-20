from __future__ import annotations

import importlib
import pkgutil
import sys

import backend


OPTIONAL_DEPENDENCIES = {
	"faiss",
	"flwr",
	"langgraph",
	"llama_cpp",
	"onnxruntime",
	"paho",
	"rank_bm25",
	"redis",
	"sentence_transformers",
	"sentencepiece",
	"tokenizers",
	"xgboost",
}


class _OptionalDependencyBlocker:
	def find_spec(self, fullname, path=None, target=None):  # type: ignore[no-untyped-def]
		if fullname.split(".", 1)[0] in OPTIONAL_DEPENDENCIES:
			raise ImportError(f"blocked optional dependency for import sweep: {fullname}")
		return None


def test_backend_modules_import_when_optional_dependencies_are_absent():
	blocker = _OptionalDependencyBlocker()
	sys.meta_path.insert(0, blocker)
	failures: list[str] = []
	try:
		for module in pkgutil.walk_packages(backend.__path__, prefix="backend."):
			if module.name.endswith(".smoke_test"):
				continue
			try:
				importlib.import_module(module.name)
			except Exception as exc:  # pragma: no cover - assertion reports details
				failures.append(f"{module.name}: {type(exc).__name__}: {exc}")
	finally:
		sys.meta_path.remove(blocker)

	assert failures == []
