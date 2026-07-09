"""Case review workflow."""

from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from components.metrics import custom_metric
from components.status_chips import chip, chips
from data.mock_data import evidence_for_case


def _selected_case(state: dict) -> dict | None:
	selected_id = state.get("selected_case_id")
	for case in state["cases"]:
		if case["case_id"] == selected_id:
			return case
	if state["cases"]:
		return state["cases"][0]
	return None


def _record_action(state: dict, case: dict, action: str, note: str = "Recorded locally on gateway; sync back queued.") -> None:
	state["audit_logs"].insert(
		0,
		{
			"case_id": case["case_id"],
			"action": action,
			"by": "PHC staff",
			"time": datetime.now().strftime("Today %H:%M"),
			"note": note,
		},
	)


@st.dialog("Override Triage Risk Level")
def override_triage_dialog(case: dict, state: dict) -> None:
	st.write(f"Current risk level: **{case['risk']}**")
	new_risk = st.selectbox("Select new risk level", ["Emergency", "High", "Moderate", "Low"])
	justification = st.text_area("Clinician justification / rationale", placeholder="Explain the reason for overriding the AI triage level...")
	if st.button("Submit Override", use_container_width=True):
		if not justification.strip():
			st.error("Justification is required to override triage.")
		else:
			old_risk = case["risk"]
			case["risk"] = new_risk
			# Update status tags (replace old risk with new risk)
			if old_risk in case["status"]:
				case["status"] = [new_risk if s == old_risk else s for s in case["status"]]
			else:
				case["status"].append(new_risk)
			_record_action(state, case, "Triage Overridden", f"Risk changed from {old_risk} to {new_risk}. Justification: {justification}")
			st.success("Triage overridden successfully.")
			st.rerun()


@st.dialog("Request More Details from ASHA")
def request_details_dialog(case: dict, state: dict) -> None:
	st.write(f"Request additional checks/details for **{case['name']}** from ASHA worker **{case['asha']}**.")
	details_requested = st.text_area("What checks or missing info are needed?", placeholder="e.g. Please check chest tightness frequency or repeat temperature in 2 hours.")
	if st.button("Assign Task to ASHA", use_container_width=True):
		if not details_requested.strip():
			st.error("Please enter details of the request.")
		else:
			new_task_id = f"T-{301 + len(state['tasks'])}"
			state["tasks"].append(
				{
					"task_id": new_task_id,
					"asha": case["asha"],
					"village": case["village"],
					"task_type": "collect missing information",
					"patient": case["name"],
					"due": "Today 18:00",
					"status": "Assigned",
				},
			)
			_record_action(state, case, "Details Requested", f"ASHA Task {new_task_id} assigned: {details_requested}")
			st.success(f"ASHA Task {new_task_id} created.")
			st.rerun()


@st.dialog("Schedule Follow-up")
def schedule_followup_dialog(case: dict, state: dict) -> None:
	st.write(f"Create follow-up task for **{case['name']}**.")
	task_type = st.selectbox("Task type", ["repeat vitals", "household follow-up", "bring patient to PHC"])
	
	c1, c2 = st.columns(2)
	due_date = c1.date_input("Due Date", value=date.today())
	due_time = c2.time_input("Due Time", value=datetime.strptime("17:00", "%H:%M").time())
	
	notes = st.text_area("Instructions for ASHA", placeholder="Enter specific instructions for this follow-up...")
	if st.button("Schedule Follow-up Task", use_container_width=True):
		due_str = f"Today {due_time.strftime('%H:%M')}" if due_date == date.today() else f"{due_date.strftime('%Y-%m-%d')} {due_time.strftime('%H:%M')}"
		new_task_id = f"T-{301 + len(state['tasks'])}"
		state["tasks"].append(
			{
				"task_id": new_task_id,
				"asha": case["asha"],
				"village": case["village"],
				"task_type": task_type,
				"patient": case["name"],
				"due": due_str,
				"status": "Assigned",
			},
		)
		if "Follow-up Due" not in case["status"]:
			case["status"].append("Follow-up Due")
		_record_action(state, case, "Follow-up Scheduled", f"ASHA Task {new_task_id} ({task_type}) scheduled. Notes: {notes}")
		st.success(f"ASHA Task {new_task_id} scheduled.")
		st.rerun()


@st.dialog("Refer Patient to Higher Facility")
def refer_patient_dialog(case: dict, state: dict) -> None:
	st.write(f"Create referral for **{case['name']}**.")
	facility = st.text_input("Referral Facility", "Community Health Centre, Barahi")
	urgency = st.selectbox("Urgency", ["Emergency", "High", "Moderate", "Planned"])
	reason = st.text_input("Reason for Referral", placeholder="e.g. persistent dyspnea, suspected complication")
	route = st.text_input("Suggested Route / Transport Details", placeholder="e.g. 12 km, ambulance advised")
	contact_notes = st.text_area("Contact / Confirmation Notes", placeholder="e.g. Nurse expected at CHC, ambulance dispatched")
	if st.button("Confirm Referral", use_container_width=True):
		if not facility.strip() or not reason.strip():
			st.error("Facility and Reason are required.")
		else:
			new_ref_id = f"R-{901 + len(state['referrals'])}"
			state["referrals"].insert(
				0,
				{
					"referral_id": new_ref_id,
					"case_id": case["case_id"],
					"patient": case["name"],
					"facility": facility,
					"urgency": urgency,
					"reason": reason,
					"route": route,
					"contact_notes": contact_notes,
					"status": "Sent",
				},
			)
			if "Referred" not in case["status"]:
				case["status"].append("Referred")
			_record_action(state, case, "Patient Referred", f"Referral {new_ref_id} created to {facility} ({urgency}).")
			st.success(f"Referral {new_ref_id} created.")
			st.rerun()


@st.dialog("Close Case")
def close_case_dialog(case: dict, state: dict) -> None:
	st.write(f"Are you sure you want to close the case for **{case['name']}**?")
	note = st.text_area("Closure notes", placeholder="e.g. Vitals stabilized, patient discharged or referral complete.")
	if st.button("Confirm Close Case", use_container_width=True):
		if "Pending Review" in case["status"]:
			case["status"].remove("Pending Review")
		if "Closed" not in case["status"]:
			case["status"].append("Closed")
		_record_action(state, case, "Case Closed", f"Case marked as closed. Notes: {note}")
		st.success("Case closed successfully.")
		st.rerun()


def render(state: dict) -> None:
	case = _selected_case(state)
	if not case:
		st.info("No cases available for review.")
		return
		
	st.caption("Selected case details, triage rationale, local evidence, actions, and audit trail.")
	st.markdown(chips(case["status"]), unsafe_allow_html=True)

	left, right = st.columns([1.35, 0.9])
	with left:
		st.subheader(f"{case['name']} · {case['case_id']}")
		
		# Clinical vitals dynamic coloring
		spo2_color = "#bc2026" if case["spo2"] < 92 else "#1f5c8f"
		hr_color = "#bc2026" if (case["heart_rate"] > 100 or case["heart_rate"] < 60) else "#1f5c8f"
		temp_color = "#bc2026" if case["temperature"] > 100.4 else "#1f5c8f"
		weight_color = "#1f5c8f"
		
		c1, c2, c3, c4 = st.columns(4)
		with c1:
			custom_metric("SpO2", f"{case['spo2']}%", spo2_color)
		with c2:
			custom_metric("Heart rate", f"{case['heart_rate']} bpm", hr_color)
		with c3:
			custom_metric("Temperature", f"{case['temperature']} F", temp_color)
		with c4:
			custom_metric("Weight", f"{case['weight']} kg", weight_color)
			
		st.markdown(
			f"""
			**Demographics & Contact**
			- **Age & Sex:** {case['age']} years · {case['sex']}
			- **Category:** {case['category']}
			- **Village:** {case['village']}
			- **ASHA Worker:** {case['asha']}
			- **Contact Phone:** {case['phone']}
			- **Household ID:** {case['household']}
			- **ASHA Worker Field Notes:** *"{case['asha_notes']}"*
			- **Reported at:** {case['timestamp']}
			- **Symptoms:** {', '.join(case['symptoms'])}
			"""
		)
		st.subheader("AI triage result")
		st.markdown(chip(case["risk"]), unsafe_allow_html=True)
		st.write(case["triage_explanation"])

	with right:
		st.subheader("PHC staff actions")
		
		is_closed = "Closed" in case["status"]
		triage_approved = "Triage Approved" in case["status"]
		
		if not is_closed:
			if st.button("Approve Triage", use_container_width=True, disabled=triage_approved):
				if "Pending Review" in case["status"]:
					case["status"].remove("Pending Review")
				if "Triage Approved" not in case["status"]:
					case["status"].append("Triage Approved")
				_record_action(state, case, "Triage Approved", f"Triage risk level of {case['risk']} approved by clinician.")
				st.success("Triage level approved.")
				st.rerun()
			if st.button("Override Triage", use_container_width=True):
				override_triage_dialog(case, state)
			if st.button("Request More Details", use_container_width=True):
				request_details_dialog(case, state)
			if st.button("Schedule Follow-up", use_container_width=True):
				schedule_followup_dialog(case, state)
			if st.button("Refer Patient", use_container_width=True):
				refer_patient_dialog(case, state)
			if st.button("Close Case", use_container_width=True):
				close_case_dialog(case, state)
		else:
			st.warning("This case is closed. Action controls are disabled.")
			if st.button("Reopen Case", use_container_width=True):
				case["status"].remove("Closed")
				if "Pending Review" not in case["status"]:
					case["status"].append("Pending Review")
				_record_action(state, case, "Case Reopened", "Case reopened by clinician.")
				st.success("Case reopened.")
				st.rerun()

	st.subheader("EdgeRAG guideline evidence")
	for item in evidence_for_case(case, state["guidelines"]):
		with st.expander(f"{item['source']} · {item['section']} · confidence {item['relevance_score']:.0%}", expanded=True):
			st.write(item["text"])

	st.subheader("Local audit trail")
	logs = [log for log in state["audit_logs"] if log["case_id"] == case["case_id"]]
	if not logs:
		st.info("No staff actions recorded for this case yet.")
	else:
		for log in logs:
			st.write(f"**{log['action']}** · {log['by']} · {log['time']}")
			st.caption(log["note"])
