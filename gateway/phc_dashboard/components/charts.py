"""Plotly chart helpers for the PHC gateway dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


CHART_COLORS = {
	"Emergency": "#bc2026",
	"High": "#c45b12",
	"Moderate": "#8a6500",
	"Low": "#16754f",
	"Pending Review": "#56605c",
	"Referred": "#1f5c8f",
	"Follow-up Due": "#6b4b00",
	"Assigned": "#1f5c8f",
	"Pending": "#c45b12",
	"Completed": "#16754f",
	"Overdue": "#bc2026",
	"Synced": "#16754f",
	"Received local": "#1f5c8f",
	"Waiting to sync back": "#c45b12",
}


def _layout(fig: go.Figure, height: int = 270) -> go.Figure:
	fig.update_layout(
		height=height,
		margin={"l": 8, "r": 8, "t": 24, "b": 8},
		paper_bgcolor="rgba(0,0,0,0)",
		plot_bgcolor="rgba(0,0,0,0)",
		font={"family": "Plus Jakarta Sans, sans-serif", "color": "#334155", "size": 12},
		legend={
			"orientation": "h",
			"yanchor": "bottom",
			"y": 1.02,
			"xanchor": "right",
			"x": 1,
		},
	)
	fig.update_xaxes(showgrid=False, zeroline=False)
	fig.update_yaxes(gridcolor="#e2e8f0", zeroline=False)
	return fig


def risk_distribution(cases: list[dict]) -> go.Figure:
	order = ["Emergency", "High", "Moderate", "Low"]
	counts = pd.Series([case["risk"] for case in cases]).value_counts().reindex(order, fill_value=0)
	df = pd.DataFrame({"Risk": counts.index, "Cases": counts.values})
	fig = px.bar(
		df,
		x="Risk",
		y="Cases",
		color="Risk",
		color_discrete_map=CHART_COLORS,
		text="Cases",
	)
	fig.update_traces(textposition="outside", marker_line_width=0)
	return _layout(fig, height=255)


def village_load(cases: list[dict]) -> go.Figure:
	df = pd.DataFrame(cases)
	grouped = df.groupby(["village", "risk"], as_index=False).size().rename(columns={"size": "Cases"})
	fig = px.bar(
		grouped,
		x="village",
		y="Cases",
		color="risk",
		color_discrete_map=CHART_COLORS,
		labels={"village": "Village", "risk": "Risk"},
	)
	return _layout(fig, height=255)


def task_status(tasks: list[dict]) -> go.Figure:
	order = ["Assigned", "Pending", "Completed", "Overdue"]
	counts = pd.Series([task["status"] for task in tasks]).value_counts().reindex(order, fill_value=0)
	fig = px.pie(
		values=counts.values,
		names=counts.index,
		hole=0.58,
		color=counts.index,
		color_discrete_map=CHART_COLORS,
	)
	fig.update_traces(textinfo="label+value", sort=False)
	return _layout(fig, height=265)


def asha_workload(tasks: list[dict]) -> go.Figure:
	df = pd.DataFrame(tasks)
	grouped = df.groupby(["asha", "status"], as_index=False).size().rename(columns={"size": "Tasks"})
	fig = px.bar(
		grouped,
		x="asha",
		y="Tasks",
		color="status",
		color_discrete_map=CHART_COLORS,
		labels={"asha": "ASHA worker", "status": "Status"},
	)
	return _layout(fig, height=265)


def sync_status(cases: list[dict]) -> go.Figure:
	df = pd.DataFrame(cases)
	counts = df["sync_status"].value_counts().reset_index()
	counts.columns = ["Sync status", "Cases"]
	fig = px.bar(
		counts,
		x="Cases",
		y="Sync status",
		orientation="h",
		color="Sync status",
		color_discrete_map=CHART_COLORS,
		text="Cases",
	)
	fig.update_traces(textposition="outside", marker_line_width=0)
	return _layout(fig, height=230)
