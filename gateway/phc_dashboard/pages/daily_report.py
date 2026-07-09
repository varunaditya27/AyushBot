import csv
from io import StringIO

import streamlit as st

from components.metrics import custom_metric


def _report_text(state: dict) -> str:
	common_symptoms = sorted({symptom for case in state["cases"] for symptom in case["symptoms"]})
	reviewed_cases = len({log["case_id"] for log in state["audit_logs"] if log.get("case_id")})
	lines = [
		f"AyushBot PHC Daily Report - {state['report_date']}",
		f"Reviewed cases: {reviewed_cases}",
		f"Emergency cases handled: {sum(1 for case in state['cases'] if case['risk'] == 'Emergency')}",
		f"Referrals made: {len(state['referrals'])}",
		f"Follow-ups scheduled: {sum(1 for task in state['tasks'] if task['status'] != 'Completed')}",
		f"Pending cases: {sum(1 for case in state['cases'] if 'Pending Review' in case['status'])}",
		f"Common symptoms: {', '.join(common_symptoms)}",
		"",
		"ASHA sync status:",
	]
	lines.extend(f"- {worker['name']} ({worker['village']}): {worker['availability']}, last sync {worker['last_sync']}" for worker in state["asha_workers"])
	return "\n".join(lines)


def _csv(state: dict) -> str:
	buffer = StringIO()
	writer = csv.DictWriter(buffer, fieldnames=["case_id", "name", "risk", "village", "asha", "sync_status"])
	writer.writeheader()
	writer.writerows({key: case[key] for key in writer.fieldnames} for case in state["cases"])
	return buffer.getvalue()


def render(state: dict) -> None:
	st.caption("End-of-day PHC operations summary for local print or export.")
	reviewed_cases = len({log["case_id"] for log in state["audit_logs"] if log.get("case_id")})
	
	cols = st.columns(5)
	with cols[0]:
		custom_metric("Reviewed cases", reviewed_cases, "#16754f")
	with cols[1]:
		custom_metric("Emergency handled", sum(1 for case in state["cases"] if case["risk"] == "Emergency"), "#bc2026")
	with cols[2]:
		custom_metric("Referrals made", len(state["referrals"]), "#1f5c8f")
	with cols[3]:
		custom_metric("Follow-ups scheduled", sum(1 for task in state["tasks"] if task["status"] != "Completed"), "#c45b12")
	with cols[4]:
		custom_metric("Pending cases", sum(1 for case in state["cases"] if "Pending Review" in case["status"]), "#56605c")

	st.subheader("Summary")
	report = _report_text(state)
	
	# Premium monospaced print preview block
	st.markdown(
		f"""
		<div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.2rem; font-family: monospace; white-space: pre-wrap; font-size: 0.9rem; color: #0f172a; line-height: 1.5; margin-bottom: 1.2rem; box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);">
{report}
		</div>
		""",
		unsafe_allow_html=True
	)
	
	c1, c2, c3 = st.columns(3)
	c1.download_button("Download text report", report, file_name="phc_daily_report.txt", mime="text/plain", use_container_width=True)
	c2.download_button("Download case CSV", _csv(state), file_name="phc_daily_cases.csv", mime="text/csv", use_container_width=True)
	html = f"<html><body><pre>{report}</pre></body></html>"
	c3.download_button("Download printable HTML", html, file_name="phc_daily_report.html", mime="text/html", use_container_width=True)
