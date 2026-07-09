"""Realistic local-first mock data for the PHC gateway dashboard."""

from __future__ import annotations

from copy import deepcopy
from datetime import date


RISK_ORDER = {"Emergency": 0, "High": 1, "Moderate": 2, "Low": 3}
RISK_COLORS = {
	"Emergency": "#bc2026",
	"High": "#c45b12",
	"Moderate": "#8a6500",
	"Low": "#16754f",
	"Pending Review": "#56605c",
	"Referred": "#1f5c8f",
	"Follow-up Due": "#6b4b00",
}


def _case_data() -> list[dict]:
	return [
		{
			"case_id": "C-2407-001",
			"patient_id": "P-1001",
			"name": "Rukmini Devi",
			"age": 28,
			"sex": "F",
			"category": "Maternal care",
			"village": "Rampur",
			"asha": "Meena Kumari",
			"phone": "98765 10001",
			"household": "HH-18A",
			"risk": "Emergency",
			"status": ["Emergency", "Pending Review"],
			"sync_status": "Received local",
			"timestamp": "Today 08:52",
			"symptoms": ["breathlessness", "fever", "dizziness"],
			"spo2": 89,
			"heart_rate": 122,
			"temperature": 101.8,
			"weight": 54.0,
			"asha_notes": "32 weeks pregnant, unable to walk without support. Family reports fever since yesterday evening.",
			"triage_explanation": "SpO2 below 92%, tachycardia, pregnancy, and breathlessness raise risk of respiratory compromise.",
			"active_flags": ["maternal care", "respiratory risk", "fever"],
			"staff_notes": "Needs immediate clinician review and referral tracking.",
		},
		{
			"case_id": "C-2407-002",
			"patient_id": "P-1002",
			"name": "Arif Khan",
			"age": 64,
			"sex": "M",
			"category": "Chronic condition",
			"village": "Kalyanpur",
			"asha": "Saira Bano",
			"phone": "98765 10002",
			"household": "HH-07C",
			"risk": "High",
			"status": ["High", "Follow-up Due"],
			"sync_status": "Waiting to sync back",
			"timestamp": "Today 09:16",
			"symptoms": ["cough", "chest pain", "fatigue"],
			"spo2": 93,
			"heart_rate": 104,
			"temperature": 99.4,
			"weight": 62.0,
			"asha_notes": "Known COPD. Missed inhaler dose. Reports chest tightness while walking.",
			"triage_explanation": "Older patient with chronic respiratory disease, chest symptoms, borderline oxygen saturation, and elevated heart rate.",
			"active_flags": ["chronic condition", "respiratory risk"],
			"staff_notes": "Repeat vitals after inhaler use; consider referral if SpO2 drops.",
		},
		{
			"case_id": "C-2407-003",
			"patient_id": "P-1003",
			"name": "Chotu Paswan",
			"age": 3,
			"sex": "M",
			"category": "Child nutrition",
			"village": "Bhavanipur",
			"asha": "Lata Devi",
			"phone": "98765 10003",
			"household": "HH-32B",
			"risk": "Moderate",
			"status": ["Moderate", "Pending Review"],
			"sync_status": "Received local",
			"timestamp": "Today 09:33",
			"symptoms": ["loose stools", "low appetite"],
			"spo2": 98,
			"heart_rate": 116,
			"temperature": 99.1,
			"weight": 10.2,
			"asha_notes": "Three loose stools since morning. Mother reports reduced feeding.",
			"triage_explanation": "Young child with gastrointestinal symptoms and low weight needs same-day review for dehydration and nutrition risk.",
			"active_flags": ["child nutrition"],
			"staff_notes": "Check hydration and feeding history.",
		},
		{
			"case_id": "C-2407-004",
			"patient_id": "P-1004",
			"name": "Sunita Oraon",
			"age": 41,
			"sex": "F",
			"category": "Fever",
			"village": "Shantipur",
			"asha": "Nirmala Singh",
			"phone": "98765 10004",
			"household": "HH-11D",
			"risk": "Low",
			"status": ["Low"],
			"sync_status": "Synced",
			"timestamp": "Today 10:06",
			"symptoms": ["mild fever", "body ache"],
			"spo2": 97,
			"heart_rate": 86,
			"temperature": 100.2,
			"weight": 48.0,
			"asha_notes": "No danger signs. Rapid malaria test not available in field kit.",
			"triage_explanation": "Mild fever with stable vitals and no reported danger signs.",
			"active_flags": ["fever"],
			"staff_notes": "Advise hydration and follow-up if fever persists.",
		},
		{
			"case_id": "C-2407-005",
			"patient_id": "P-1005",
			"name": "Mahesh Yadav",
			"age": 52,
			"sex": "M",
			"category": "General",
			"village": "Rampur",
			"asha": "Meena Kumari",
			"phone": "98765 10005",
			"household": "HH-21F",
			"risk": "High",
			"status": ["High", "Referred"],
			"sync_status": "Waiting to sync back",
			"timestamp": "Today 10:18",
			"symptoms": ["high fever", "confusion"],
			"spo2": 95,
			"heart_rate": 118,
			"temperature": 103.4,
			"weight": 59.0,
			"asha_notes": "Family says patient is not responding normally. PHC visit advised.",
			"triage_explanation": "High fever with altered sensorium is a danger sign requiring urgent PHC assessment.",
			"active_flags": ["fever"],
			"staff_notes": "PHC observation and escalation if sensorium worsens.",
		},
	]


def _guidelines() -> list[dict]:
	return [
		{
			"id": "G-01",
			"source": "MoHFW Maternal Health Field Manual",
			"section": "Pregnancy danger signs",
			"last_updated": "2025-11-18",
			"relevance_score": 0.94,
			"text": "Pregnant patients with breathlessness, persistent fever, dizziness, or oxygen saturation below normal range should receive urgent facility assessment.",
			"tags": ["maternal care", "respiratory risk", "fever"],
		},
		{
			"id": "G-02",
			"source": "WHO IMCI Pocket Book",
			"section": "Assess dehydration in children",
			"last_updated": "2024-09-12",
			"relevance_score": 0.88,
			"text": "Children with diarrhoea require assessment for lethargy, drinking ability, skin pinch, weight trajectory, and signs of dehydration.",
			"tags": ["child nutrition"],
		},
		{
			"id": "G-03",
			"source": "NPCDCS Respiratory Care Note",
			"section": "COPD danger symptoms",
			"last_updated": "2025-03-01",
			"relevance_score": 0.82,
			"text": "Older adults with chronic respiratory disease and worsening chest symptoms should be prioritized when oxygen saturation is borderline or heart rate is elevated.",
			"tags": ["chronic condition", "respiratory risk"],
		},
		{
			"id": "G-04",
			"source": "Integrated Disease Surveillance Fever Desk Guide",
			"section": "Fever with altered sensorium",
			"last_updated": "2025-07-22",
			"relevance_score": 0.91,
			"text": "High fever accompanied by confusion, reduced responsiveness, seizure, or neck stiffness warrants urgent clinician review and referral consideration.",
			"tags": ["fever"],
		},
	]


def initial_state() -> dict:
	cases = _case_data()
	return {
		"cases": cases,
		"patients": cases,
		"asha_workers": [
			{"name": "Meena Kumari", "village": "Rampur", "availability": "Available", "last_sync": "Today 09:42"},
			{"name": "Saira Bano", "village": "Kalyanpur", "availability": "Field visit", "last_sync": "Today 09:10"},
			{"name": "Lata Devi", "village": "Bhavanipur", "availability": "Offline", "last_sync": "Yesterday 18:20"},
			{"name": "Nirmala Singh", "village": "Shantipur", "availability": "Available", "last_sync": "Today 10:02"},
		],
		"referrals": [
			{"referral_id": "R-901", "case_id": "C-2407-001", "patient": "Rukmini Devi", "facility": "Community Health Centre, Barahi", "urgency": "Emergency", "reason": "Maternal respiratory distress", "route": "12 km via SH-6, ambulance advised", "contact_notes": "Dr. Patil informed at 09:04", "status": "Sent"},
			{"referral_id": "R-902", "case_id": "C-2407-005", "patient": "Mahesh Yadav", "facility": "PHC Observation Room", "urgency": "High", "reason": "High fever with confusion", "route": "4 km by family vehicle", "contact_notes": "Nurse desk expecting patient", "status": "Accepted"},
			{"referral_id": "R-903", "case_id": "C-2407-002", "patient": "Arif Khan", "facility": "District Hospital Pulmonology", "urgency": "Planned", "reason": "COPD review after PHC stabilization", "route": "27 km, bus route 2 then auto", "contact_notes": "Referral note pending", "status": "Planned"},
		],
		"tasks": [
			{"task_id": "T-301", "asha": "Saira Bano", "village": "Kalyanpur", "task_type": "repeat vitals", "patient": "Arif Khan", "due": "Today 14:00", "status": "Pending"},
			{"task_id": "T-302", "asha": "Lata Devi", "village": "Bhavanipur", "task_type": "household follow-up", "patient": "Chotu Paswan", "due": "Today 16:00", "status": "Assigned"},
			{"task_id": "T-303", "asha": "Meena Kumari", "village": "Rampur", "task_type": "referral confirmation", "patient": "Rukmini Devi", "due": "Today 10:30", "status": "Overdue"},
			{"task_id": "T-304", "asha": "Nirmala Singh", "village": "Shantipur", "task_type": "collect missing information", "patient": "Sunita Oraon", "due": "Tomorrow 10:00", "status": "Completed"},
		],
		"guidelines": _guidelines(),
		"sync_events": [
			{"event_id": "S-001", "type": "Case received", "detail": "C-2407-001 from Meena Kumari", "village": "Rampur", "status": "Complete", "time": "08:53"},
			{"event_id": "S-002", "type": "Back sync pending", "detail": "Triage approval for Arif Khan", "village": "Kalyanpur", "status": "Queued", "time": "09:31"},
			{"event_id": "S-003", "type": "Failed sync", "detail": "Voice note attachment for C-2407-003", "village": "Bhavanipur", "status": "Retrying", "time": "09:37"},
			{"event_id": "S-004", "type": "Duplicate conflict", "detail": "Sunita Oraon may match P-0884", "village": "Shantipur", "status": "Needs resolution", "time": "10:07"},
		],
		"audit_logs": [
			{"case_id": "C-2407-001", "action": "Emergency referral created", "by": "Dr. Kavita Rao", "time": "Today 09:06", "note": "CHC informed, ambulance requested."},
			{"case_id": "C-2407-002", "action": "Follow-up requested", "by": "Nurse Anil", "time": "Today 09:45", "note": "Repeat SpO2 after inhaler use."},
			{"case_id": "C-2407-005", "action": "Triage approved", "by": "Dr. Kavita Rao", "time": "Today 10:23", "note": "High fever with confusion; PHC observation."},
		],
		"selected_case_id": "C-2407-001",
		"report_date": date.today().isoformat(),
	}


def fresh_state() -> dict:
	return deepcopy(initial_state())


def evidence_for_case(case: dict, guidelines: list[dict]) -> list[dict]:
	flags = set(case.get("active_flags", []))
	matches = [item for item in guidelines if flags.intersection(item.get("tags", []))]
	return sorted(matches or guidelines[:2], key=lambda item: item["relevance_score"], reverse=True)
