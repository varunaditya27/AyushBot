"""Outbreak Detection Dashboard Page."""

import streamlit as st

st.title("🔴 Outbreak Detection")

st.markdown(
    """
### Real-time Case & Referral Monitoring
- Case trends by district
- Outbreak hotspot map
- Referral patterns
- Alert triggers
"""
)

# Placeholder metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Cases (24h)", "2,450", "+12%")
col2.metric("Total Referrals (24h)", "340", "+5%")
col3.metric("Active Outbreaks", "3", "→")
col4.metric("Alert Severity", "Medium", "⚠️")

st.info("Implementation coming in Phase 3.2")
