"""AyushBot PHC Gateway Web Dashboard."""

from __future__ import annotations

import streamlit as st

from data.mock_data import fresh_state
from pages import asha_tasks, case_review, daily_report, guidelines, local_sync, patients, queue, referrals


PAGES = {
	"Queue": queue.render,
	"Case Review": case_review.render,
	"Patients": patients.render,
	"Referrals": referrals.render,
	"ASHA Tasks": asha_tasks.render,
	"Local Sync": local_sync.render,
	"Guidelines": guidelines.render,
	"Daily Report": daily_report.render,
}


def _init_state() -> None:
	if "phc_data" not in st.session_state:
		st.session_state.phc_data = fresh_state()
	if "loading_demo" not in st.session_state:
		st.session_state.loading_demo = False
	if "error_demo" not in st.session_state:
		st.session_state.error_demo = False


def _style() -> None:
	st.markdown(
		"""
		<style>
		@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
		
		/* Font styling */
		html, body, .stApp, .stMarkdown, p, label, input, textarea, select, button {
			font-family: 'Plus Jakarta Sans', sans-serif !important;
		}
		
		.block-container {
			padding-top: 1.5rem !important;
			padding-bottom: 3rem !important;
			max-width: 1200px !important;
		}
		
		/* Custom premium card design for custom metrics */
		.metric-card {
			background-color: #ffffff !important;
			border: 1px solid #eef2f5 !important;
			border-radius: 12px !important;
			padding: 1rem 1.2rem !important;
			box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.02), 0 4px 6px -2px rgba(0, 0, 0, 0.01) !important;
			transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
		}
		
		.metric-card:hover {
			transform: translateY(-2px) !important;
			box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04), 0 8px 10px -6px rgba(0, 0, 0, 0.02) !important;
		}
		
		/* Sidebar styling */
		[data-testid="stSidebar"] {
			background-color: #f8fafc !important;
			border-right: 1px solid #e2e8f0 !important;
		}
		
		[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
			font-weight: 700 !important;
			color: #0f172a !important;
		}
		
		[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
			font-weight: 700 !important;
			color: #475569 !important;
			letter-spacing: 0.05em !important;
			text-transform: uppercase !important;
			font-size: 0.75rem !important;
		}
		
		[data-testid="stSidebar"] div[class*="stRadio"] label p {
			font-size: 0.95rem !important;
			color: #334155 !important;
			font-weight: 500 !important;
		}
		
		/* Premium styled buttons */
		div.stButton > button {
			background-color: #ffffff !important;
			color: #0f172a !important;
			border: 1px solid #cbd5e1 !important;
			border-radius: 8px !important;
			padding: 0.45rem 0.9rem !important;
			font-weight: 500 !important;
			box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.04) !important;
			transition: all 0.2s ease !important;
		}
		
		div.stButton > button:hover {
			background-color: #f8fafc !important;
			border-color: #94a3b8 !important;
			color: #0f172a !important;
			transform: translateY(-1px) !important;
			box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
		}
		
		/* Form container */
		[data-testid="stForm"] {
			background-color: #ffffff !important;
			border: 1px solid #e2e8f0 !important;
			border-radius: 12px !important;
			padding: 1.5rem !important;
			box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.01) !important;
		}
		
		/* Expanders */
		.streamlit-expanderHeader {
			background-color: #ffffff !important;
			border: 1px solid #e2e8f0 !important;
			border-radius: 8px !important;
			font-weight: 600 !important;
			color: #334155 !important;
		}
		
		/* Sidebar compact alerts */
		[data-testid="stSidebar"] div[data-testid="stAlert"] {
			padding: 0.5rem 0.8rem !important;
			margin-top: 0.4rem !important;
			margin-bottom: 0.4rem !important;
			border-radius: 8px !important;
			border: none !important;
		}
		
		.small-note { color: #64748b; font-size: 0.85rem; }
		.section-rule { border-top: 1px solid #e2e8f0; margin: 1.2rem 0; }
		</style>
		""",
		unsafe_allow_html=True,
	)


def _sidebar() -> str:
	st.sidebar.title("AyushBot PHC Gateway")
	st.sidebar.caption("Offline-first local clinical operations")
	st.sidebar.markdown("---")
	page = st.sidebar.radio("Navigation", list(PAGES), index=0)
	st.sidebar.markdown("---")
	st.sidebar.caption("Gateway PHC-RPI-004")
	st.sidebar.success("Local store available")
	st.sidebar.info("Cloud sync queued until network window")
	st.sidebar.toggle("Show loading state", key="loading_demo")
	st.sidebar.toggle("Show error state", key="error_demo")
	return page


def main() -> None:
	st.set_page_config(
		page_title="AyushBot PHC Gateway",
		page_icon="🏥",
		layout="wide",
		initial_sidebar_state="expanded",
	)
	_init_state()
	_style()
	page = _sidebar()

	st.title(page)
	if st.session_state.loading_demo:
		st.info("Loading local gateway data from the Raspberry Pi store...")
	if st.session_state.error_demo:
		st.error("Local sync reader is unavailable. Showing cached PHC mock data; offline workflows remain usable.")

	PAGES[page](st.session_state.phc_data)


if __name__ == "__main__":
	main()
