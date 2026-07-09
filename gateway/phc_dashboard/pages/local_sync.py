import pandas as pd
import streamlit as st
import re

from components.metrics import custom_metric


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
	st.dataframe(pd.DataFrame(events), use_container_width=True, hide_index=True)

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
		
		# Dynamically parse conflict details from detail text (e.g., "Sunita Oraon may match P-0884")
		detail_str = selected_conflict["detail"]
		match = re.match(r"(.*?) may match (P-\d+)", detail_str)
		
		new_info = "New incoming patient details"
		exist_info = "Existing patient profile details"
		new_name = "Sunita Oraon"
		existing_id = "P-0884"
		
		if match:
			new_name = match.group(1).strip()
			existing_id = match.group(2).strip()
			
			new_pat = next((p for p in state["patients"] if p["name"] == new_name), None)
			exist_pat = next((p for p in state["patients"] if p["patient_id"] == existing_id), None)
			
			if new_pat:
				new_info = f"<b>Name:</b> {new_pat['name']}<br><b>Age/Sex:</b> {new_pat['age']}{new_pat['sex']}<br><b>Village:</b> {new_pat['village']}<br><b>Household:</b> {new_pat['household']}<br><b>Phone:</b> {new_pat['phone']}<br><b>Reported:</b> {new_pat['timestamp']}"
			else:
				new_info = f"<b>Name:</b> {new_name}<br>No additional details found on gateway."
				
			if exist_pat:
				exist_info = f"<b>ID:</b> {exist_pat['patient_id']}<br><b>Name:</b> {exist_pat['name']}<br><b>Age/Sex:</b> {exist_pat['age']}{exist_pat['sex']}<br><b>Village:</b> {exist_pat['village']}<br><b>Household:</b> {exist_pat['household']}<br><b>Phone:</b> {exist_pat['phone']}"
			else:
				exist_info = f"<b>ID:</b> {existing_id}<br>No existing record details found on gateway."

		with st.form("duplicate-resolution-form"):
			st.markdown(f"**Resolving:** {selected_conflict['detail']}")
			
			col_left, col_right = st.columns(2)
			with col_left:
				st.markdown(
					f"""
					<div style="background-color: #f8fafc; padding: 1.2rem; border-radius: 8px; border: 1px solid #e2e8f0; height: 160px;">
						<strong style="color: #16754f; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">New Incoming Record</strong>
						<p style="margin: 0.6rem 0 0 0; font-size: 0.9rem; line-height: 1.4; color: #334155;">{new_info}</p>
					</div>
					""",
					unsafe_allow_html=True
				)
			with col_right:
				st.markdown(
					f"""
					<div style="background-color: #f8fafc; padding: 1.2rem; border-radius: 8px; border: 1px solid #e2e8f0; height: 160px;">
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
					# Update matching patient data in state
					for patient in state["patients"]:
						if patient["name"] == new_name:
							patient["name"] = exist_pat["name"] if exist_pat else "Sunita Uran"
							patient["patient_id"] = existing_id
							patient["age"] = exist_pat["age"] if exist_pat else 42
							patient["staff_notes"] = (patient["staff_notes"] or "") + f"\n[System] Merged record with {existing_id}."
					for case in state["cases"]:
						if case["name"] == new_name:
							case["name"] = exist_pat["name"] if exist_pat else "Sunita Uran"
							case["patient_id"] = existing_id
							case["age"] = exist_pat["age"] if exist_pat else 42
				elif choice == "Keep separate":
					# Assign new ID to keep them separate
					for patient in state["patients"]:
						if patient["name"] == new_name:
							patient["patient_id"] = f"P-{1000 + len(state['patients'])}"
				
				st.success(f"Conflict resolution saved locally: {choice}.")
				st.rerun()

	st.subheader("Last successful sync by ASHA worker and village")
	st.dataframe(pd.DataFrame(state["asha_workers"]), use_container_width=True, hide_index=True)
