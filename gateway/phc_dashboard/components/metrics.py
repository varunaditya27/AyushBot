"""Compact metric rows for PHC operations."""

from __future__ import annotations

import html

import streamlit as st


def custom_metric(label: str, value: str | int, border_color: str) -> None:
	safe_label = html.escape(str(label))
	safe_value = html.escape(str(value))
	st.markdown(
		f"""
		<div class="metric-card" style="border-left: 4px solid {border_color} !important;">
			<div style="color: #64748b; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1.2;">{safe_label}</div>
			<div style="color: #0f172a; font-size: 1.6rem; font-weight: 700; margin-top: 0.25rem; line-height: 1.2; white-space: normal; overflow-wrap: anywhere;">{safe_value}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def queue_metrics(cases: list[dict], referrals: list[dict], tasks: list[dict]) -> None:
	emergency = sum(1 for case in cases if case["risk"] == "Emergency")
	pending = sum(1 for case in cases if "Pending Review" in case["status"])
	followups = sum(1 for case in cases if "Follow-up Due" in case["status"])
	followups += sum(1 for task in tasks if task["status"] == "Overdue")

	cols = st.columns(5)
	with cols[0]:
		custom_metric("Cases today", len(cases), "#16754f")
	with cols[1]:
		custom_metric("Emergency", emergency, "#bc2026")
	with cols[2]:
		custom_metric("Pending reviews", pending, "#56605c")
	with cols[3]:
		custom_metric("Referrals", len(referrals), "#1f5c8f")
	with cols[4]:
		custom_metric("Follow-ups due", followups, "#c45b12")
