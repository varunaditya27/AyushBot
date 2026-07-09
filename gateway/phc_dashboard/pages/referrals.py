"""Referral workflow management."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st


STATUSES = ["Planned", "Sent", "Accepted", "Completed", "Cancelled"]


def _summary(referral: dict) -> str:
	return "\n".join(
		[
			"AyushBot PHC Referral Summary",
			f"Referral ID: {referral['referral_id']}",
			f"Case ID: {referral['case_id']}",
			f"Patient: {referral['patient']}",
			f"Facility: {referral['facility']}",
			f"Urgency: {referral['urgency']}",
			f"Reason: {referral['reason']}",
			f"Route/distance: {referral['route']}",
			f"Contact notes: {referral['contact_notes']}",
			f"Status: {referral['status']}",
		]
	)


def render(state: dict) -> None:
	st.caption("Operational referral tracking for PHC staff.")

	tabs = st.tabs(["Referral Queue", "Create Referral", "Referral Directory"])

	with tabs[0]:
		if not state["referrals"]:
			st.info("No active referrals in the queue.")
		else:
			for referral in state["referrals"]:
				with st.expander(f"{referral['referral_id']} · {referral['patient']} · {referral['facility']} ({referral['urgency']})", expanded=True):
					c1, c2, c3 = st.columns([1, 1, 1])
					c1.write(f"**Reason:** {referral['reason']}")
					c2.write(f"**Route:** {referral['route']}")
					c3.write(f"**Contact notes:** {referral['contact_notes']}")
					
					new_status = st.selectbox(
						"Update Status",
						STATUSES,
						index=STATUSES.index(referral["status"]),
						key=f"ref-status-{referral['referral_id']}",
					)
					if new_status != referral["status"]:
						referral["status"] = new_status
						case_id = referral.get("case_id")
						if case_id and case_id != "Manual":
							state["audit_logs"].insert(
								0,
								{
									"case_id": case_id,
									"action": "Referral Status Updated",
									"by": "PHC staff",
									"time": "Today " + datetime.now().strftime("%H:%M"),
									"note": f"Referral {referral['referral_id']} status changed to {new_status}.",
								},
							)
						st.success(f"Status of {referral['referral_id']} updated to {new_status}.")
						st.rerun()

					st.download_button(
						"Download Referral Summary",
						_summary(referral),
						file_name=f"{referral['referral_id']}_referral_summary.txt",
						mime="text/plain",
						key=f"dl-btn-{referral['referral_id']}",
					)

	with tabs[1]:
		st.subheader("Manual Referral Form")
		patients = sorted(state["patients"], key=lambda patient: (patient["name"], patient["patient_id"]))
		selected_patient_id = st.selectbox(
			"Select Patient",
			[patient["patient_id"] for patient in patients],
			format_func=lambda patient_id: next(
				f"{patient['name']} ({patient['patient_id']})"
				for patient in patients
				if patient["patient_id"] == patient_id
			),
		)
		selected_patient = next(patient for patient in patients if patient["patient_id"] == selected_patient_id)
		
		patient_cases = [
			case["case_id"]
			for case in state["cases"]
			if case.get("patient_id") == selected_patient_id
		]
		case_id = st.selectbox("Select Associated Case (Optional)", ["None"] + patient_cases)
		
		facility = st.text_input("Facility Name", "Community Health Centre, Barahi")
		urgency = st.selectbox("Urgency Level", ["Emergency", "High", "Moderate", "Planned"])
		reason = st.text_input("Clinical Reason for Referral", placeholder="Explain the primary symptom or diagnosis...")
		route = st.text_input("Suggested Route / Distance / Mode", placeholder="e.g. 12 km via SH-6, ambulance confirmation requested")
		contact_notes = st.text_area("Contact & Confirmation Notes", placeholder="e.g. Doctor notified, confirmation code: 4920")
		
		submit = st.button("Submit Referral", width="stretch")
		if submit:
			if not facility.strip() or not reason.strip():
				st.error("Facility and Reason are required to create a referral.")
			else:
				new_ref_id = f"R-{901 + len(state['referrals'])}"
				actual_case_id = None if case_id == "None" else case_id
				state["referrals"].insert(
					0,
					{
						"referral_id": new_ref_id,
						"case_id": actual_case_id or "Manual",
						"patient": selected_patient["name"],
						"patient_id": selected_patient_id,
						"facility": facility,
						"urgency": urgency,
						"reason": reason,
						"route": route,
						"contact_notes": contact_notes,
						"status": "Sent",
					},
				)
				
				if actual_case_id:
					case = next(c for c in state["cases"] if c["case_id"] == actual_case_id)
					if "Referred" not in case["status"]:
						case["status"].append("Referred")
					state["audit_logs"].insert(
						0,
						{
							"case_id": actual_case_id,
							"action": "Patient Referred",
							"by": "PHC staff",
							"time": "Today " + datetime.now().strftime("%H:%M"),
							"note": f"Referral {new_ref_id} created to {facility} ({urgency}).",
						},
					)
				st.success(f"Referral {new_ref_id} successfully created and sent!")
				st.rerun()

	with tabs[2]:
		st.subheader("Referral History Log")
		if not state["referrals"]:
			st.info("No referrals recorded.")
		else:
			df = pd.DataFrame(state["referrals"])
			st.dataframe(df, width="stretch", hide_index=True)
