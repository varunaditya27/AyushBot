import pandas as pd
import streamlit as st

from components import charts
from components.metrics import custom_metric
from datetime import date, datetime, timedelta


TASK_TYPES = ["repeat vitals", "household follow-up", "bring patient to PHC", "collect missing information", "referral confirmation"]
STATUSES = ["Assigned", "Pending", "Completed", "Overdue"]


def _format_due(due_date: date, due_time) -> str:
	if due_date == date.today():
		return f"Today {due_time.strftime('%H:%M')}"
	return f"{due_date.strftime('%Y-%m-%d')} {due_time.strftime('%H:%M')}"


def _parse_due(value: str) -> tuple[date, object]:
	parts = value.split()
	due_date = date.today()
	due_time = datetime.strptime("17:00", "%H:%M").time()
	if len(parts) >= 2:
		if parts[0] == "Tomorrow":
			due_date = date.today() + timedelta(days=1)
		elif parts[0] != "Today":
			try:
				due_date = datetime.strptime(parts[0], "%Y-%m-%d").date()
			except ValueError:
				due_date = date.today()
		try:
			due_time = datetime.strptime(parts[1], "%H:%M").time()
		except ValueError:
			due_time = datetime.strptime("17:00", "%H:%M").time()
	return due_date, due_time


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
			due_str = _format_due(due_date, due_time)
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

	chart_left, chart_right = st.columns([0.9, 1.1])
	with chart_left:
		with st.container(border=True):
			st.markdown("**Task Status Mix**")
			st.plotly_chart(charts.task_status(state["tasks"]), width="stretch", config={"displayModeBar": False})
	with chart_right:
		with st.container(border=True):
			st.markdown("**ASHA Workload**")
			st.plotly_chart(charts.asha_workload(state["tasks"]), width="stretch", config={"displayModeBar": False})

	st.subheader("Task Management Registry")
	st.write("Review task details below, then use the update controls to change status or due time without shifting rows.")
	
	df = pd.DataFrame(state["tasks"]).sort_values(by="task_id", ascending=False)
	st.dataframe(
		df,
		column_config={
			"task_id": st.column_config.TextColumn("Task ID", disabled=True),
			"asha": st.column_config.TextColumn("ASHA Worker", disabled=True),
			"village": st.column_config.TextColumn("Village", disabled=True),
			"task_type": st.column_config.TextColumn("Task Type", disabled=True),
			"patient": st.column_config.TextColumn("Patient", disabled=True),
			"due": st.column_config.TextColumn("Due Date/Time", disabled=True),
			"status": st.column_config.TextColumn("Status", disabled=True),
		},
		width="stretch",
		hide_index=True,
	)

	if state["tasks"]:
		task_by_id = {task["task_id"]: task for task in state["tasks"]}
		selected_task_id = st.selectbox(
			"Select task to update",
			[task["task_id"] for task in sorted(state["tasks"], key=lambda item: item["task_id"], reverse=True)],
			format_func=lambda task_id: f"{task_id} - {task_by_id[task_id]['patient']} ({task_by_id[task_id]['status']})",
		)
		selected_task = task_by_id[selected_task_id]
		current_due_date, current_due_time = _parse_due(selected_task["due"])
		with st.form("update-task"):
			c1, c2, c3 = st.columns(3)
			next_status = c1.selectbox("Status", STATUSES, index=STATUSES.index(selected_task["status"]))
			next_due_date = c2.date_input("Due Date", value=current_due_date)
			next_due_time = c3.time_input("Due Time", value=current_due_time)
			if st.form_submit_button("Update selected task"):
				selected_task["status"] = next_status
				selected_task["due"] = _format_due(next_due_date, next_due_time)
				st.success(f"{selected_task_id} updated locally.")
				st.rerun()

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
		width="stretch",
		hide_index=True
	)
