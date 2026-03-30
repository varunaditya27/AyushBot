"""Smoke test for llama.cpp engine with JSON grammar."""

from __future__ import annotations

import os
import sys

from pydantic import BaseModel, Field

from backend.llm.engine import create_engine


class PingResponse(BaseModel):
    message: str = Field(..., min_length=1)


def main() -> int:
    try:
        engine = create_engine()
    except FileNotFoundError as exc:
        print(f"[skip] {exc}")
        return 0
    except Exception as exc:
        print(f"[error] failed to init engine: {exc}")
        return 1

    prompt = os.getenv("AYUSHBOT_LLM_SAMPLE_PROMPT", 'Return JSON: {"message": "ok"}')
    try:
        output = engine.generate_json(prompt, PingResponse, max_tokens=64)
        print(output.strip())
        return 0
    except Exception as exc:
        print(f"[error] inference failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
