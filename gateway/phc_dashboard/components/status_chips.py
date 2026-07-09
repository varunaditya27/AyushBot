"""Status chip helpers for Streamlit markdown."""

from __future__ import annotations

import html

from data.mock_data import RISK_COLORS


def chip(label: str) -> str:
	color = RISK_COLORS.get(label, "#56605c")
	return (
		f"<span style='display:inline-block;margin:2px 4px 2px 0;padding:2px 8px;"
		f"border-radius:999px;background:{color}1a;color:{color};"
		f"border:1px solid {color}55;font-size:0.78rem;font-weight:700;'>"
		f"{html.escape(label)}</span>"
	)


def chips(labels: list[str]) -> str:
	return " ".join(chip(label) for label in labels)
