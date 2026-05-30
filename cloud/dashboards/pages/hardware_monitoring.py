"""Hardware Monitoring Dashboard Page."""

import streamlit as st

st.title("📱 Hardware Monitoring")

st.markdown(
    """
### Gateway Health & Status
- Device battery levels
- Signal strength (WiFi/Cellular)
- Last sync timestamps
- Connectivity status
"""
)

# Placeholder status
col1, col2, col3 = st.columns(3)
col1.metric("Gateways Online", "47/50", "94%")
col2.metric("Avg Battery", "73%", "-5%")
col3.metric("Connectivity", "Good", "✅")

st.info("Implementation coming in Phase 3.3")
