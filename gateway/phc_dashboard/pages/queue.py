"""Live PHC case queue."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.metrics import queue_metrics
from components.status_chips import chips
from data.mock_data import RISK_ORDER


def _options(rows: list[dict], key: str) -> list[str]:
	return ["All"] + sorted({row[key] for row in rows})


def render(state: dict) -> None:
	cases = state["cases"]
	st.caption("Today’s ASHA-submitted cases, sorted by emergency and high-risk cases first.")
	queue_metrics(cases, state["referrals"], state["tasks"])

	st.sidebar.markdown("### Queue filters")
	village = st.sidebar.selectbox("Village", _options(cases, "village"))
	asha = st.sidebar.selectbox("ASHA worker", _options(cases, "asha"))
	risk = st.sidebar.selectbox("Risk level", ["All", "Emergency", "High", "Moderate", "Low"])
	category = st.sidebar.selectbox("Patient category", _options(cases, "category"))
	sync_status = st.sidebar.selectbox("Sync status", _options(cases, "sync_status"))

	filtered = [
		case
		for case in cases
		if (village == "All" or case["village"] == village)
		and (asha == "All" or case["asha"] == asha)
		and (risk == "All" or case["risk"] == risk)
		and (category == "All" or case["category"] == category)
		and (sync_status == "All" or case["sync_status"] == sync_status)
	]
	filtered.sort(key=lambda case: (RISK_ORDER[case["risk"]], case["timestamp"]))

	if not filtered:
		st.info("No cases match the current filters.")
		return

	table_rows = [
		{
			"Time": case["timestamp"].replace("Today ", ""),
			"Case": case["case_id"],
			"Patient": f"{case['name']} ({case['age']}{case['sex']})",
			"Village": case["village"],
			"ASHA": case["asha"],
			"Risk": case["risk"],
			"Status": ", ".join(case["status"]),
			"Sync": case["sync_status"],
			"Vitals": f"SpO2 {case['spo2']}%, HR {case['heart_rate']}, {case['temperature']} F",
		}
		for case in filtered
	]
	st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

	selected = st.selectbox("Select case for review", [case["case_id"] for case in filtered], format_func=lambda cid: f"{cid} - {next(c['name'] for c in filtered if c['case_id'] == cid)}")
	state["selected_case_id"] = selected
	st.markdown(chips(next(case["status"] for case in filtered if case["case_id"] == selected)), unsafe_allow_html=True)
	st.info("Open the Case Review page to act on the selected case.")
