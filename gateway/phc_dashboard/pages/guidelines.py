"""Local EdgeRAG evidence viewer."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data.mock_data import evidence_for_case


def render(state: dict) -> None:
	st.caption("Search locally stored guideline chunks and inspect the evidence used in recommendations.")
	query = st.text_input("Search guideline documents", placeholder="maternal, fever, dehydration, COPD")
	needle = query.lower().strip()
	rows = [
		item
		for item in state["guidelines"]
		if not needle or needle in " ".join([item["source"], item["section"], item["text"], " ".join(item["tags"])]).lower()
	]
	if rows:
		st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
	else:
		st.info("No local guideline chunk matches this search.")

	case = next(case for case in state["cases"] if case["case_id"] == state["selected_case_id"])
	st.subheader("Retrieved chunks used in recommendation")
	for item in evidence_for_case(case, state["guidelines"]):
		with st.expander(f"{item['source']} · {item['section']} · relevance {item['relevance_score']:.0%}", expanded=True):
			st.write(item["text"])
			st.caption(f"Last updated: {item['last_updated']}")

	st.subheader("Why AyushBot suggested this")
	st.info(f"For {case['name']}, AyushBot matched vitals, ASHA notes, active flags ({', '.join(case['active_flags'])}), and local EdgeRAG chunks. The risk was assigned as {case['risk']} because: {case['triage_explanation']}")
