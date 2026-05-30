"""Aggregation Rounds History Dashboard Page."""

import streamlit as st

st.title("⏱️ Aggregation Rounds History")

st.markdown(
    """
### FL Training Round Timeline
- Round progression timeline
- Client participation rates
- Aggregation metrics
- Model version downloads
"""
)

# Placeholder stats
col1, col2, col3 = st.columns(3)
col1.metric("Completed Rounds", "127", "+1")
col2.metric("Avg Clients/Round", "42", "→")
col3.metric("Aggregation Time", "3.2s", "-0.1s")

st.info("Implementation coming in Phase 3.5")
