"""AyushBot PHC Gateway Web Dashboard."""

from __future__ import annotations

import streamlit as st

from data.mock_data import fresh_state
from pages import asha_tasks, case_review, daily_report, guidelines, local_sync, patients, queue, referrals


PAGES = {
	"Live Queue": queue.render,
	"Case Review": case_review.render,
	"Patient Registry": patients.render,
	"Referrals": referrals.render,
	"ASHA Tasks": asha_tasks.render,
	"Local Sync": local_sync.render,
	"Guidelines": guidelines.render,
	"Daily Report": daily_report.render,
}

PAGE_SUBTITLES = {
	"Live Queue": "ASHA-submitted cases, clinical risk, vitals, and sync status for today.",
	"Case Review": "Clinician action workspace for triage decisions, evidence, and audit trail.",
	"Patient Registry": "Searchable local records, clinical flags, visits, and staff notes.",
	"Referrals": "Track higher-facility referrals from creation through completion.",
	"ASHA Tasks": "Coordinate follow-ups, field checks, and local task sync.",
	"Local Sync": "Monitor offline backlog, failed syncs, and duplicate patient conflicts.",
	"Guidelines": "Inspect local EdgeRAG guideline chunks used for recommendations.",
	"Daily Report": "End-of-day PHC operations summary for export and handover.",
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

		.stApp {
			background:
				radial-gradient(circle at 18% 0%, rgba(20, 184, 166, 0.14) 0%, rgba(20, 184, 166, 0) 28%),
				radial-gradient(circle at 90% 18%, rgba(37, 99, 235, 0.12) 0%, rgba(37, 99, 235, 0) 28%),
				linear-gradient(180deg, rgba(239, 246, 255, 0.92) 0%, rgba(248, 250, 252, 0.98) 34%, #ffffff 100%) !important;
		}
		
		.block-container {
			padding-top: 1.1rem !important;
			padding-bottom: 3rem !important;
			max-width: 1320px !important;
		}

		h1, h2, h3 {
			letter-spacing: 0 !important;
		}

		h2, h3 {
			color: #0f3f4f !important;
		}

		div[data-testid="stCaptionContainer"] {
			color: #52606d !important;
		}

		.phc-hero {
			background:
				linear-gradient(135deg, rgba(15, 118, 110, 0.96) 0%, rgba(21, 94, 117, 0.96) 48%, rgba(29, 78, 216, 0.96) 100%),
				radial-gradient(circle at 12% 20%, rgba(255,255,255,0.32), rgba(255,255,255,0) 28%);
			border: 1px solid rgba(255,255,255,0.42);
			border-radius: 18px;
			padding: 1.35rem 1.45rem;
			box-shadow: 0 18px 42px -28px rgba(15, 23, 42, 0.45);
			margin-bottom: 1.1rem;
			color: #ffffff;
		}

		.phc-hero h1 {
			margin: 0 !important;
			color: #ffffff !important;
			font-size: 2rem !important;
			line-height: 1.1 !important;
		}

		.phc-hero p {
			margin: 0.45rem 0 0 0 !important;
			color: rgba(255,255,255,0.86) !important;
			font-size: 0.98rem !important;
			max-width: 820px;
		}

		.phc-hero-row {
			display: flex;
			align-items: flex-start;
			justify-content: space-between;
			gap: 1rem;
			flex-wrap: wrap;
		}

		.phc-hero-badges {
			display: flex;
			gap: 0.45rem;
			flex-wrap: wrap;
			justify-content: flex-end;
		}

		.phc-badge {
			display: inline-flex;
			align-items: center;
			border-radius: 999px;
			padding: 0.34rem 0.7rem;
			background: rgba(255,255,255,0.16);
			border: 1px solid rgba(255,255,255,0.28);
			color: #ffffff;
			font-size: 0.8rem;
			font-weight: 700;
			white-space: nowrap;
		}
		
		/* Custom premium card design for custom metrics */
		.metric-card {
			background: linear-gradient(180deg, #ffffff 0%, #f5fbfa 100%) !important;
			border: 1px solid rgba(203, 213, 225, 0.86) !important;
			border-radius: 10px !important;
			padding: 1rem 1.2rem !important;
			box-shadow: 0 12px 30px -24px rgba(15, 23, 42, 0.38) !important;
			transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
			min-height: 100px;
		}
		
		.metric-card:hover {
			transform: translateY(-2px) !important;
			box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.04), 0 8px 10px -6px rgba(0, 0, 0, 0.02) !important;
		}
		
		/* Sidebar styling */
		[data-testid="stSidebar"] {
			background:
				radial-gradient(circle at 20% 8%, rgba(20, 184, 166, 0.18) 0%, rgba(20, 184, 166, 0) 26%),
				linear-gradient(180deg, #f8fafc 0%, #edf7f4 52%, #eef4ff 100%) !important;
			border-right: 1px solid rgba(148, 163, 184, 0.35) !important;
			box-shadow: inset -1px 0 0 rgba(255,255,255,0.75) !important;
		}
		
		[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
			font-weight: 700 !important;
			color: #0f172a !important;
		}

		[data-testid="stSidebar"] h1 {
			background: linear-gradient(90deg, #0f766e 0%, #1d4ed8 100%);
			-webkit-background-clip: text;
			background-clip: text;
			color: transparent !important;
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
			color: inherit !important;
			font-weight: 700 !important;
		}

		[data-testid="stSidebar"] [role="radiogroup"] {
			display: flex;
			flex-direction: column;
			gap: 0.42rem;
		}

		[data-testid="stSidebar"] [role="radiogroup"] label {
			position: relative;
			display: flex !important;
			align-items: center !important;
			gap: 0.65rem !important;
			min-height: 42px;
			padding: 0.55rem 0.72rem !important;
			border-radius: 12px !important;
			border: 1px solid rgba(148, 163, 184, 0.34) !important;
			background: rgba(255,255,255,0.66) !important;
			box-shadow: 0 10px 22px -22px rgba(15, 23, 42, 0.45) !important;
			color: #334155 !important;
			transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease !important;
		}

		[data-testid="stSidebar"] [role="radiogroup"] label:hover {
			transform: translateX(3px);
			border-color: rgba(20, 184, 166, 0.55) !important;
			background: linear-gradient(90deg, rgba(240, 253, 250, 0.94), rgba(239, 246, 255, 0.94)) !important;
			box-shadow: 0 12px 28px -22px rgba(15, 118, 110, 0.5) !important;
		}

		[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
			background: linear-gradient(135deg, #0f766e 0%, #1d4ed8 100%) !important;
			border-color: rgba(255,255,255,0.58) !important;
			color: #ffffff !important;
			box-shadow: 0 14px 30px -20px rgba(29, 78, 216, 0.72) !important;
		}

		[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::before {
			content: "";
			position: absolute;
			left: -6px;
			top: 9px;
			bottom: 9px;
			width: 4px;
			border-radius: 999px;
			background: #14b8a6;
			box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.18);
		}

		[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {
			transform: scale(0.9);
			filter: saturate(1.35);
		}
		
		/* Premium styled buttons */
		div.stButton > button {
			background: linear-gradient(90deg, rgba(240, 253, 250, 0.96) 0%, #ffffff 58%, rgba(239, 246, 255, 0.96) 100%) !important;
			color: #0f172a !important;
			border: 1px solid rgba(14, 116, 144, 0.24) !important;
			border-radius: 10px !important;
			padding: 0.55rem 0.95rem !important;
			font-weight: 700 !important;
			box-shadow: 0 10px 22px -20px rgba(15, 23, 42, 0.5) !important;
			transition: all 0.2s ease !important;
		}
		
		div.stButton > button:hover {
			background: linear-gradient(135deg, #0f766e 0%, #1d4ed8 100%) !important;
			border-color: rgba(255,255,255,0.4) !important;
			color: #ffffff !important;
			transform: translateY(-2px) !important;
			box-shadow: 0 16px 30px -20px rgba(29, 78, 216, 0.72) !important;
		}

		div.stDownloadButton > button {
			background: linear-gradient(135deg, #0f766e 0%, #1d4ed8 100%) !important;
			color: #ffffff !important;
			border: 1px solid rgba(255,255,255,0.26) !important;
			border-radius: 10px !important;
			font-weight: 800 !important;
			box-shadow: 0 14px 28px -20px rgba(29, 78, 216, 0.7) !important;
		}
		
		/* Form container */
		[data-testid="stForm"] {
			background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(240,253,250,0.78) 100%) !important;
			border: 1px solid rgba(20, 184, 166, 0.22) !important;
			border-radius: 12px !important;
			padding: 1.5rem !important;
			box-shadow: 0 14px 34px -28px rgba(15, 23, 42, 0.5) !important;
		}
		
		/* Expanders */
		.streamlit-expanderHeader {
			background: linear-gradient(90deg, #ffffff 0%, #f0fdfa 100%) !important;
			border: 1px solid rgba(20, 184, 166, 0.22) !important;
			border-radius: 8px !important;
			font-weight: 600 !important;
			color: #334155 !important;
		}
		
		/* Sidebar compact alerts */
		[data-testid="stSidebar"] div[data-testid="stAlert"] {
			padding: 0.78rem 0.9rem !important;
			margin-top: 0.4rem !important;
			margin-bottom: 0.75rem !important;
			border-radius: 12px !important;
			border: none !important;
			box-shadow: 0 14px 28px -24px rgba(15, 23, 42, 0.45) !important;
		}
		
		.small-note { color: #64748b; font-size: 0.85rem; }
		.section-rule { border-top: 1px solid #e2e8f0; margin: 1.2rem 0; }

		[data-testid="stDataFrame"] {
			border: 1px solid rgba(14, 116, 144, 0.22);
			border-radius: 10px;
			overflow: hidden;
			box-shadow: 0 12px 28px -24px rgba(15, 23, 42, 0.5);
		}

		[data-testid="stVerticalBlockBorderWrapper"] {
			background: linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,250,252,0.96) 100%) !important;
			border: 1px solid rgba(14, 116, 144, 0.18) !important;
			box-shadow: 0 14px 34px -30px rgba(15, 23, 42, 0.45) !important;
		}

		[data-baseweb="select"] > div,
		[data-testid="stTextInput"] input,
		[data-testid="stTextArea"] textarea,
		[data-testid="stDateInput"] input,
		[data-testid="stTimeInput"] input {
			border-color: rgba(14, 116, 144, 0.28) !important;
			background: rgba(255,255,255,0.82) !important;
			border-radius: 10px !important;
		}

		[data-baseweb="select"] > div:focus-within,
		[data-testid="stTextInput"] input:focus,
		[data-testid="stTextArea"] textarea:focus {
			border-color: #0f766e !important;
			box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.14) !important;
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def _sidebar() -> str:
	st.sidebar.title("AyushBot")
	st.sidebar.caption("PHC Gateway Command Center")
	st.sidebar.markdown("---")
	page = st.sidebar.radio("Navigation", list(PAGES), index=0)
	st.sidebar.markdown("---")
	st.sidebar.markdown("### System Status")
	st.sidebar.success("Local store available")
	st.sidebar.info("Cloud sync queued until network window")
	st.sidebar.caption("Gateway PHC-RPI-004")
	st.sidebar.toggle("Show loading state", key="loading_demo")
	st.sidebar.toggle("Show error state", key="error_demo")
	return page


def _page_header(page: str) -> None:
	st.markdown(
		f"""
		<div class="phc-hero">
			<div class="phc-hero-row">
				<div>
					<h1>{page}</h1>
					<p>{PAGE_SUBTITLES[page]}</p>
				</div>
				<div class="phc-hero-badges">
					<span class="phc-badge">Offline-first</span>
					<span class="phc-badge">PHC-RPI-004</span>
					<span class="phc-badge">EdgeRAG ready</span>
				</div>
			</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


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

	_page_header(page)
	if st.session_state.loading_demo:
		st.info("Loading local gateway data from the Raspberry Pi store...")
	if st.session_state.error_demo:
		st.error("Local sync reader is unavailable. Showing cached PHC mock data; offline workflows remain usable.")

	PAGES[page](st.session_state.phc_data)


if __name__ == "__main__":
	main()
