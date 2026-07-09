import html
import pandas as pd
import streamlit as st
import re

from components.metrics import custom_metric


def _patient_card(patient: dict | None, fallback_title: str, fallback_detail: str) -> str:
	if not patient:
		return f"<b>{html.escape(fallback_title)}:</b> {html.escape(fallback_detail)}<br>No additional details found on gateway."
	return (
		f"<b>ID:</b> {html.escape(str(patient.get('patient_id', 'Unknown')))}<br>"
		f"<b>Name:</b> {html.escape(str(patient.get('name', 'Unknown')))}<br>"
		f"<b>Age/Sex:</b> {html.escape(str(patient.get('age', '')))}{html.escape(str(patient.get('sex', '')))}<br>"
		f"<b>Village:</b> {html.escape(str(patient.get('village', 'Unknown')))}<br>"
		f"<b>Household:</b> {html.escape(str(patient.get('household', 'Unknown')))}<br>"
		f"<b>Phone:</b> {html.escape(str(patient.get('phone', 'Unknown')))}"
	)


def render(state: dict) -> None:
	st.caption("ASHA phone sync state, offline backlog, failed items, and duplicate patient conflict resolution.")
	events = state["sync_events"]
	
	cols = st.columns(5)
	with cols[0]:
		custom_metric("Cases received", sum(1 for event in events if event["type"] == "Case received"), "#16754f")
	with cols[1]:
		custom_metric("Waiting sync back", sum(1 for case in state["cases"] if case["sync_status"] == "Waiting to sync back"), "#c45b12")
	with cols[2]:
		custom_metric("Failed syncs", sum(1 for event in events if event["type"] == "Failed sync"), "#bc2026")
	with cols[3]:
		custom_metric("Duplicate conflicts", sum(1 for event in events if "Duplicate conflict" in event["type"] and event["status"] == "Needs resolution"), "#bc2026")
	with cols[4]:
		custom_metric("Offline backlog", sum(1 for case in state["cases"] if case["sync_status"] != "Synced"), "#56605c")

	st.subheader("Sync event log")
	st.dataframe(pd.DataFrame(events), width="stretch", hide_index=True)

	st.subheader("Duplicate patient conflict")
	conflicts = [e for e in events if "Duplicate conflict" in e["type"] and e["status"] == "Needs resolution"]
	
	if not conflicts:
		st.success("All patient duplicate conflicts have been resolved successfully!")
	else:
		selected_conflict = st.selectbox(
			"Select duplicate conflict to resolve",
			conflicts,
			format_func=lambda c: f"{c['detail']} ({c['village']})"
		)
		
		detail_str = selected_conflict["detail"]
		match = re.match(r"(.*?) may match (P-\d+)", detail_str)
		
		new_name = ""
		existing_id = ""
		new_pat = None
		exist_pat = None
		
		if match:
			new_name = match.group(1).strip()
			existing_id = match.group(2).strip()
			
			new_pat = next((p for p in state["patients"] if p["name"] == new_name), None)
			exist_pat = next((p for p in state["patients"] if p["patient_id"] == existing_id), None)
			new_info = _patient_card(new_pat, "Incoming name", new_name)
			exist_info = _patient_card(exist_pat, "Existing ID", existing_id)
		else:
			new_info = _patient_card(None, "Conflict detail", detail_str)
			exist_info = _patient_card(None, "Existing profile", "Unable to parse from conflict detail")

		with st.form("duplicate-resolution-form"):
			st.markdown(f"**Resolving:** {html.escape(selected_conflict['detail'])}")
			
			col_left, col_right = st.columns(2)
			with col_left:
				st.markdown(
					f"""
					<div style="background-color: #f8fafc; padding: 1.2rem; border-radius: 8px; border: 1px solid #e2e8f0; min-height: 160px;">
						<strong style="color: #16754f; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">New Incoming Record</strong>
						<p style="margin: 0.6rem 0 0 0; font-size: 0.9rem; line-height: 1.4; color: #334155;">{new_info}</p>
					</div>
					""",
					unsafe_allow_html=True
				)
			with col_right:
				st.markdown(
					f"""
					<div style="background-color: #f8fafc; padding: 1.2rem; border-radius: 8px; border: 1px solid #e2e8f0; min-height: 160px;">
						<strong style="color: #475569; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Existing Patient Profile</strong>
						<p style="margin: 0.6rem 0 0 0; font-size: 0.9rem; line-height: 1.4; color: #334155;">{exist_info}</p>
					</div>
					""",
					unsafe_allow_html=True
				)
			
			st.markdown(
				"""
				<div style="margin: 1rem 0 0 0; padding: 0.4rem 0.6rem; background: #f0fdf4; border-radius: 6px; border: 1px solid #bbf7d0; display: inline-block;">
					<span style="color: #16754f; font-weight: 700; font-size: 0.85rem;">AI Match Confidence: 86%</span>
				</div>
				""",
				unsafe_allow_html=True
			)
			
			choice = st.radio("Resolution Action", ["Merge records", "Keep separate", "Ask ASHA to verify"], horizontal=True)
			if st.form_submit_button("Save resolution"):
				selected_conflict["status"] = "Resolved"
				selected_conflict["detail"] += f" - Resolved: {choice}"
				
				if choice == "Merge records":
					for patient in state["patients"]:
						if patient["name"] == new_name:
							patient["name"] = exist_pat["name"] if exist_pat else patient["name"]
							patient["patient_id"] = existing_id
							patient["age"] = exist_pat["age"] if exist_pat else patient["age"]
							patient["staff_notes"] = (patient["staff_notes"] or "") + f"\n[System] Merged record with {existing_id}."
					for case in state["cases"]:
						if case["name"] == new_name:
							case["name"] = exist_pat["name"] if exist_pat else case["name"]
							case["patient_id"] = existing_id
							case["age"] = exist_pat["age"] if exist_pat else case["age"]
				elif choice == "Keep separate":
					for patient in state["patients"]:
						if patient["name"] == new_name:
							patient["patient_id"] = f"P-{1000 + len(state['patients'])}"
				
				st.success(f"Conflict resolution saved locally: {choice}.")
				st.rerun()

	st.subheader("Last successful sync by ASHA worker and village")
	st.dataframe(pd.DataFrame(state["asha_workers"]), width="stretch", hide_index=True)
