"""AyushBot Analytics Dashboard - Main Streamlit App."""

import sys
from pathlib import Path

import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Configure Streamlit app
st.set_page_config(
    page_title="AyushBot Analytics",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for styling
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #f0f2f6;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🏥 AyushBot")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Select Page",
    [
        "🔴 Outbreak Detection",
        "📱 Hardware Monitoring",
        "📈 Model Drift Analysis",
        "⏱️ Aggregation History",
    ],
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
### System Status
- **FL Server**: Running (port 8080)
- **Dashboard**: Running (port 8501)
- **InfluxDB**: Connected
- **PostgreSQL**: Connected
"""
)

# Main content area
if page == "🔴 Outbreak Detection":
    st.title("Outbreak Detection Dashboard")
    st.info("Loading outbreak detection metrics...")
    st.write("Coming soon in Phase 3.2")

elif page == "📱 Hardware Monitoring":
    st.title("Hardware Monitoring Dashboard")
    st.info("Loading gateway health metrics...")
    st.write("Coming soon in Phase 3.3")

elif page == "📈 Model Drift Analysis":
    st.title("Model Drift Analysis Dashboard")
    st.info("Loading model performance trends...")
    st.write("Coming soon in Phase 3.4")

elif page == "⏱️ Aggregation History":
    st.title("Aggregation Rounds History")
    st.info("Loading FL round history...")
    st.write("Coming soon in Phase 3.5")

st.markdown("---")
st.markdown("© 2026 AyushBot Analytics | Federated Learning Health Platform")
