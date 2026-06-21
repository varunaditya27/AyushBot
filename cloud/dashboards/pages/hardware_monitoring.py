"""Hardware Monitoring Dashboard Page - Gateway Health & Status."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboards.db_helpers import PostgreSQLConnection

st.set_page_config(page_title="Hardware Monitoring", page_icon="📱", layout="wide")

# Configure page
st.title("📱 Hardware Monitoring Dashboard")
st.markdown("Real-time gateway health and connectivity status across all PHCs")
st.markdown("---")


@st.cache_data(ttl=60)  # Cache for 1 minute (frequent updates)
def get_gateway_status_from_postgres(
    client: PostgreSQLConnection, limit: int = 500
) -> pd.DataFrame:
    """Query gateway status from PostgreSQL.

    Args:
        client: PostgreSQLConnection instance
        limit: Maximum records to return

    Returns:
        DataFrame with columns: device_id, phc_id, district, battery_pct, signal_strength,
                               connectivity_status, last_sync, uptime_hours, model
    """
    try:
        logs = client.query_audit_logs(limit=limit)

        if not logs:
            return pd.DataFrame()

        records = []
        for log in logs:
            # Parse log entry (id, timestamp, event_type, details)
            # In real implementation, details would be JSON with device metrics
            records.append(
                {
                    "device_id": f"GW{log[0]:03d}" if log[0] else "GW000",
                    "phc_id": f"PHC{(log[0] % 50) + 1:03d}" if log[0] else "PHC001",
                    "timestamp": log[1],
                }
            )

        return pd.DataFrame(records)
    except Exception as e:
        st.warning(f"⚠️ PostgreSQL connection error: {str(e)}")
        return generate_mock_gateway_data()


def generate_mock_gateway_data(num_gateways: int = 50) -> pd.DataFrame:
    """Generate realistic mock gateway hardware data for testing.

    Args:
        num_gateways: Number of gateways to generate

    Returns:
        DataFrame with gateway hardware metrics
    """
    import numpy as np

    districts = [
        "North Delhi",
        "South Delhi",
        "East Delhi",
        "West Delhi",
        "Central Delhi",
        "New Delhi",
    ]
    models = ["RaspberryPi4", "RaspberryPi5", "Jetson Nano", "Orange Pi"]

    records = []
    for i in range(num_gateways):
        device_id = f"GW{i + 1:03d}"
        phc_id = f"PHC{(i % 50) + 1:03d}"
        district = districts[i % len(districts)]

        # Realistic battery level (normal distribution around 75%)
        battery = min(100, max(0, int(np.random.normal(75, 15))))

        # Signal strength in dBm (-30 to -100, higher is better)
        signal = int(np.random.normal(-60, 15))
        signal = min(-30, max(-100, signal))

        # Connectivity status based on signal strength
        if signal > -70:
            status = "Online"
        elif signal > -85:
            status = "Degraded"
        else:
            status = "Offline"

        # Last sync time (minutes ago)
        last_sync_minutes = int(abs(np.random.exponential(scale=30)))

        # Uptime (hours)
        uptime = int(np.random.exponential(scale=500))

        # Model
        model = models[i % len(models)]

        records.append(
            {
                "device_id": device_id,
                "phc_id": phc_id,
                "district": district,
                "battery_pct": battery,
                "signal_strength": signal,
                "connectivity_status": status,
                "last_sync_minutes": last_sync_minutes,
                "uptime_hours": uptime,
                "model": model,
            }
        )

    return pd.DataFrame(records)


# Sidebar filters
with st.sidebar:
    st.subheader("🔍 Filters")

    status_filter = st.multiselect(
        "Connectivity Status",
        options=["Online", "Degraded", "Offline"],
        default=["Online", "Degraded", "Offline"],
    )

    battery_threshold = st.slider(
        "Battery Alert Threshold (%)",
        min_value=0,
        max_value=100,
        value=20,
        help="Highlight gateways below this level",
    )

    signal_threshold = st.slider(
        "Signal Strength Threshold (dBm)",
        min_value=-100,
        max_value=-30,
        value=-75,
        help="Threshold for poor signal (-100 = weakest, -30 = strongest)",
    )

    last_sync_threshold = st.slider(
        "Last Sync Threshold (minutes)",
        min_value=1,
        max_value=1440,
        value=60,
        help="Alert if not synced within N minutes",
    )

# Load data
postgresql_client = PostgreSQLConnection()
df = generate_mock_gateway_data()

# Filter by selected status
df = df[df["connectivity_status"].isin(status_filter)]

if not df.empty:
    # Calculate overall metrics
    total_gateways = len(df)
    online_count = len(df[df["connectivity_status"] == "Online"])
    degraded_count = len(df[df["connectivity_status"] == "Degraded"])
    offline_count = len(df[df["connectivity_status"] == "Offline"])

    avg_battery = df["battery_pct"].mean()
    avg_signal = df["signal_strength"].mean()

    low_battery = len(df[df["battery_pct"] <= battery_threshold])
    poor_signal = len(df[df["signal_strength"] <= signal_threshold])
    stale_sync = len(df[df["last_sync_minutes"] > last_sync_threshold])

    online_pct = (online_count / total_gateways * 100) if total_gateways > 0 else 0

    # Display key metrics
    st.subheader("📊 System Health Overview")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Gateways Online", f"{online_count}/{total_gateways}", f"{online_pct:.1f}%")
    col2.metric("Avg Battery", f"{avg_battery:.0f}%", f"{low_battery} low" if low_battery > 0 else "All good")
    col3.metric("Avg Signal", f"{avg_signal:.0f} dBm", f"{poor_signal} weak" if poor_signal > 0 else "All good")
    col4.metric("Stale Syncs", f"{stale_sync}", "⚠️" if stale_sync > 0 else "✅")

    st.markdown("---")

    # Status summary cards
    st.subheader("🔴 Connectivity Status")
    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        st.metric(
            "🟢 Online",
            online_count,
            f"{(online_count / total_gateways * 100):.1f}%" if total_gateways > 0 else "0%",
        )

    with status_col2:
        st.metric(
            "🟡 Degraded",
            degraded_count,
            f"{(degraded_count / total_gateways * 100):.1f}%" if total_gateways > 0 else "0%",
        )

    with status_col3:
        st.metric(
            "🔴 Offline",
            offline_count,
            f"{(offline_count / total_gateways * 100):.1f}%" if total_gateways > 0 else "0%",
        )

    st.markdown("---")

    # Battery distribution gauge
    st.subheader("🔋 Battery Level Distribution")
    battery_col1, battery_col2 = st.columns(2)

    with battery_col1:
        # Battery distribution histogram
        fig_battery = px.histogram(
            df,
            x="battery_pct",
            nbins=20,
            title="Battery Distribution Across Gateways",
            color_discrete_sequence=["#FF6B6B"],
            labels={"battery_pct": "Battery %", "count": "Number of Gateways"},
        )
        fig_battery.add_vline(
            x=battery_threshold,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Alert Threshold ({battery_threshold}%)",
        )
        st.plotly_chart(fig_battery, use_container_width=True)

    with battery_col2:
        # Battery gauge for overall fleet
        fig_gauge = go.Figure(
            data=[
                go.Indicator(
                    mode="gauge+number+delta",
                    value=avg_battery,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Fleet Avg Battery"},
                    delta={"reference": 50},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "darkblue"},
                        "steps": [
                            {"range": [0, 20], "color": "lightgray"},
                            {"range": [20, 50], "color": "gray"},
                            {"range": [50, 80], "color": "lightgreen"},
                            {"range": [80, 100], "color": "green"},
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 4},
                            "thickness": 0.75,
                            "value": battery_threshold,
                        },
                    },
                )
            ]
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.markdown("---")

    # Signal strength visualization
    st.subheader("📶 Signal Strength Analysis")
    signal_col1, signal_col2 = st.columns(2)

    with signal_col1:
        # Signal histogram
        fig_signal = px.histogram(
            df,
            x="signal_strength",
            nbins=20,
            title="Signal Strength Distribution",
            color_discrete_sequence=["#4ECDC4"],
            labels={"signal_strength": "Signal (dBm)", "count": "Number of Gateways"},
        )
        fig_signal.add_vline(
            x=signal_threshold,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Poor Signal Threshold ({signal_threshold} dBm)",
        )
        st.plotly_chart(fig_signal, use_container_width=True)

    with signal_col2:
        # Signal by status
        signal_by_status = (
            df.groupby("connectivity_status")["signal_strength"]
            .mean()
            .reset_index()
            .sort_values("signal_strength", ascending=False)
        )

        fig_status_signal = px.bar(
            signal_by_status,
            x="connectivity_status",
            y="signal_strength",
            title="Avg Signal by Connectivity Status",
            color="signal_strength",
            color_continuous_scale="RdYlGn",
            labels={"signal_strength": "Avg Signal (dBm)", "connectivity_status": "Status"},
        )
        st.plotly_chart(fig_status_signal, use_container_width=True)

    st.markdown("---")

    # Device details table
    st.subheader("🖥️ Gateway Devices - Detailed View")

    # Create display dataframe with formatted columns
    display_df = df.copy()
    display_df["battery_pct"] = display_df["battery_pct"].apply(lambda x: f"{x}%")
    display_df["signal_strength"] = display_df["signal_strength"].apply(lambda x: f"{x} dBm")
    display_df["last_sync_minutes"] = display_df["last_sync_minutes"].apply(
        lambda x: f"{x}m ago" if x < 60 else f"{x // 60}h {x % 60}m ago"
    )
    display_df["uptime_hours"] = display_df["uptime_hours"].apply(
        lambda x: f"{x // 24}d {x % 24}h" if x >= 24 else f"{x}h"
    )

    # Reorder columns for display
    display_columns = [
        "device_id",
        "phc_id",
        "district",
        "model",
        "connectivity_status",
        "battery_pct",
        "signal_strength",
        "last_sync_minutes",
        "uptime_hours",
    ]
    st.dataframe(
        display_df[display_columns],
        use_container_width=True,
        hide_index=True,
    )

    # Alerts section
    st.markdown("---")
    st.subheader("⚠️ Alert Summary")

    alert_data = []

    # Low battery devices
    low_battery_df = df[df["battery_pct"] <= battery_threshold].sort_values(
        "battery_pct"
    )
    if not low_battery_df.empty:
        alert_data.append(
            {
                "Type": "🔋 Low Battery",
                "Count": len(low_battery_df),
                "Devices": ", ".join(low_battery_df["device_id"].head(3).tolist()),
            }
        )

    # Poor signal devices
    poor_signal_df = df[df["signal_strength"] <= signal_threshold].sort_values(
        "signal_strength"
    )
    if not poor_signal_df.empty:
        alert_data.append(
            {
                "Type": "📶 Weak Signal",
                "Count": len(poor_signal_df),
                "Devices": ", ".join(poor_signal_df["device_id"].head(3).tolist()),
            }
        )

    # Stale sync
    stale_df = df[df["last_sync_minutes"] > last_sync_threshold].sort_values(
        "last_sync_minutes", ascending=False
    )
    if not stale_df.empty:
        alert_data.append(
            {
                "Type": "🔄 Stale Sync",
                "Count": len(stale_df),
                "Devices": ", ".join(stale_df["device_id"].head(3).tolist()),
            }
        )

    # Offline devices
    offline_df = df[df["connectivity_status"] == "Offline"]
    if not offline_df.empty:
        alert_data.append(
            {
                "Type": "🔴 Offline",
                "Count": len(offline_df),
                "Devices": ", ".join(offline_df["device_id"].head(3).tolist()),
            }
        )

    if alert_data:
        alert_df = pd.DataFrame(alert_data)
        st.dataframe(alert_df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ All gateways operating normally!")

else:
    st.error("❌ No gateway data available.")
    st.info("💡 Displaying mock data for demonstration purposes.")
    df = generate_mock_gateway_data()
    st.dataframe(df.head(20), use_container_width=True)

st.markdown("---")
st.markdown("Last updated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
