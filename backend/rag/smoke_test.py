"""Smoke test for ONNX + FAISS retriever.

Run locally after placing the ONNX model and FAISS index on disk.
"""

from __future__ import annotations

import os
import sys

from backend.rag.retriever import create_retriever


def main() -> int:
    try:
        retriever = create_retriever()
    except FileNotFoundError as exc:
        print(f"[skip] {exc}")
        return 0
    except Exception as exc:
        print(f"[error] failed to init retriever: {exc}")
        return 1

    sample_query = os.getenv("AYUSHBOT_RAG_SAMPLE_QUERY", "cough and fast breathing")
    result = retriever.query(sample_query)
    print({"guardrail_triggered": result["guardrail_triggered"], "count": len(result["results"])})
    return 0


if __name__ == "__main__":
    sys.exit(main())
