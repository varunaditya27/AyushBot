import pandas as pd
import streamlit as st

from components.metrics import custom_metric
from datetime import date, datetime


TASK_TYPES = ["repeat vitals", "household follow-up", "bring patient to PHC", "collect missing information", "referral confirmation"]
STATUSES = ["Assigned", "Pending", "Completed", "Overdue"]


def render(state: dict) -> None:
	st.caption("Coordinate PHC follow-ups with ASHA workers. Sync status is local workflow context, not fleet monitoring.")
	
	st.subheader("Assign Task to ASHA")
	with st.form("assign-task", clear_on_submit=True):
		c1, c2, c3, c4, c5 = st.columns(5)
		asha = c1.selectbox("ASHA worker", [worker["name"] for worker in state["asha_workers"]])
		task_type = c2.selectbox("Task type", TASK_TYPES)
		patient = c3.selectbox("Patient", [case["name"] for case in state["cases"]])
		due_date = c4.date_input("Due Date", value=date.today())
		due_time = c5.time_input("Due Time", value=datetime.strptime("17:00", "%H:%M").time())
		submitted = st.form_submit_button("Assign task")
		if submitted:
			worker = next(item for item in state["asha_workers"] if item["name"] == asha)
			due_str = f"Today {due_time.strftime('%H:%M')}" if due_date == date.today() else f"{due_date.strftime('%Y-%m-%d')} {due_time.strftime('%H:%M')}"
			state["tasks"].append(
				{"task_id": f"T-{301 + len(state['tasks'])}", "asha": asha, "village": worker["village"], "task_type": task_type, "patient": patient, "due": due_str, "status": "Assigned"},
			)
			st.success("Task assigned locally and queued for ASHA sync.")
			st.rerun()

	# Compute metrics
	c1, c2, c3, c4 = st.columns(4)
	with c1:
		custom_metric("Assigned", sum(1 for task in state["tasks"] if task["status"] == "Assigned"), "#1f5c8f")
	with c2:
		custom_metric("Pending", sum(1 for task in state["tasks"] if task["status"] == "Pending"), "#c45b12")
	with c3:
		custom_metric("Completed", sum(1 for task in state["tasks"] if task["status"] == "Completed"), "#16754f")
	with c4:
		custom_metric("Overdue", sum(1 for task in state["tasks"] if task["status"] == "Overdue"), "#bc2026")

	st.subheader("Task Management Registry")
	st.write("Edit status or due time inline in the table below to update the task status on the gateway.")
	
	df = pd.DataFrame(state["tasks"]).sort_values(by="task_id", ascending=False)
	edited_df = st.data_editor(
		df,
		column_config={
			"task_id": st.column_config.TextColumn("Task ID", disabled=True),
			"asha": st.column_config.TextColumn("ASHA Worker", disabled=True),
			"village": st.column_config.TextColumn("Village", disabled=True),
			"task_type": st.column_config.SelectboxColumn("Task Type", options=TASK_TYPES, required=True),
			"patient": st.column_config.TextColumn("Patient", disabled=True),
			"due": st.column_config.TextColumn("Due Date/Time", required=True),
			"status": st.column_config.SelectboxColumn("Status", options=STATUSES, required=True),
		},
		use_container_width=True,
		hide_index=True,
		key="tasks_editor"
	)
	
	# Dynamically sync changes back to state["tasks"]
	state["tasks"] = edited_df.to_dict("records")

	st.subheader("ASHA Worker Directory & Sync Info")
	asha_df = pd.DataFrame(state["asha_workers"])
	st.dataframe(
		asha_df,
		column_config={
			"name": "ASHA Worker",
			"village": "Village Coverage",
			"availability": "Availability Status",
			"last_sync": "Last Successful Sync",
		},
		use_container_width=True,
		hide_index=True
	)
