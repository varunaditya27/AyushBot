"""Local patient registry."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from components.status_chips import chip


def render(state: dict) -> None:
	st.caption("Searchable local patient registry stored on the PHC gateway.")
	query = st.text_input("Search by name, ID, village, phone, household, or ASHA worker")
	needle = query.lower().strip()
	patients = [
		patient
		for patient in state["patients"]
		if not needle
		or needle in " ".join(str(patient[field]) for field in ["name", "patient_id", "village", "phone", "household", "asha"]).lower()
	]
	if not patients:
		st.info("No local patient record matches this search.")
		return

	rows = []
	for patient in patients:
		referrals = [ref for ref in state["referrals"] if ref["patient"] == patient["name"]]
		rows.append(
			{
				"Patient ID": patient["patient_id"],
				"Name": patient["name"],
				"Village": patient["village"],
				"Phone": patient["phone"],
				"Household": patient["household"],
				"ASHA": patient["asha"],
				"Active flags": ", ".join(patient["active_flags"]),
				"Risk history": patient["risk"],
				"Previous referrals": referrals[0]["status"] if referrals else "None",
			}
		)
	
	st.write("**Matching Patient Records:**")
	st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

	st.markdown("---")
	st.subheader("Patient Clinical File View")
	selected_patient_id = st.selectbox(
		"Select patient to view clinical file",
		[patient["patient_id"] for patient in patients],
		format_func=lambda pid: f"{next(p['name'] for p in patients if p['patient_id'] == pid)} ({pid})"
	)

	if selected_patient_id:
		patient = next(p for p in state["patients"] if p["patient_id"] == selected_patient_id)
		col1, col2 = st.columns([1.2, 0.8])
		
		with col1:
			st.markdown(f"### {patient['name']} (ID: {patient['patient_id']})")
			st.markdown(
				f"""
				**Demographics & Location**
				- **Age & Sex:** {patient['age']} years · {patient['sex']}
				- **Category:** {patient['category']}
				- **Village:** {patient['village']}
				- **Household:** {patient['household']}
				- **Phone:** {patient['phone']}
				- **ASHA Worker:** {patient['asha']}
				"""
			)
			st.write("**Active clinical flags:**")
			if patient["active_flags"]:
				st.markdown(" ".join(chip(flag) for flag in patient["active_flags"]), unsafe_allow_html=True)
			else:
				st.write("None")

			st.write("**Visit History & Vitals Log:**")
			vitals_history = [
				{
					"Date": patient["timestamp"],
					"SpO2": f"{patient['spo2']}%",
					"Heart Rate": patient["heart_rate"],
					"Temperature": f"{patient['temperature']} F",
					"Weight": f"{patient['weight']} kg",
					"Notes": patient["asha_notes"],
				},
				{
					"Date": "1 week ago",
					"SpO2": f"{min(99, patient['spo2'] + 1)}%",
					"Heart Rate": max(78, patient['heart_rate'] - 4),
					"Temperature": "98.6 F",
					"Weight": f"{patient['weight'] - 0.2:.1f} kg",
					"Notes": "Routine follow-up check",
				},
			]
			st.table(pd.DataFrame(vitals_history))

		with col2:
			st.markdown("### Clinical Notes & History")
			st.write(f"**Risk history:** {patient['risk']}")

			referrals = [ref for ref in state["referrals"] if ref["patient"] == patient["name"]]
			st.write("**Previous referrals:**")
			if referrals:
				for ref in referrals:
					st.markdown(f"- **{ref['referral_id']}** to {ref['facility']} ({ref['urgency']}): **{ref['status']}**")
			else:
				st.write("No referrals recorded.")

			st.write("**Staff Clinical Notes:**")
			st.info(patient["staff_notes"] or "No clinical notes on record.")

			with st.form("add_clinical_note", clear_on_submit=True):
				new_note = st.text_area("Append clinical staff note", placeholder="Write comments, observations, or instructions...")
				if st.form_submit_button("Append Note"):
					if new_note.strip():
						timestamp = datetime.now().strftime("%d %b %H:%M")
						updated_notes = f"{patient['staff_notes']}\n[{timestamp}] {new_note}" if patient["staff_notes"] else f"[{timestamp}] {new_note}"
						patient["staff_notes"] = updated_notes
						st.success("Note appended successfully.")
						st.rerun()
