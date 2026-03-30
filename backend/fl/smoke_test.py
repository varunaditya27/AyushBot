"""Smoke test for Flower FL client wiring."""

from __future__ import annotations

import sys

from backend.fl.fl_client import create_client


def main() -> int:
    client = create_client()
    params = client.get_parameters({})
    print({"params_len": len(params), "first_param_size": params[0].size if params else 0})
    return 0


if __name__ == "__main__":
    sys.exit(main())
