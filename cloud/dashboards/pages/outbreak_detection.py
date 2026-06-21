"""Outbreak Detection Dashboard Page - Real-time Case & Referral Monitoring."""

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

from dashboards.db_helpers import InfluxDBConnection

st.set_page_config(page_title="Outbreak Detection", page_icon="🔴", layout="wide")

# Configure page
st.title("🔴 Outbreak Detection Dashboard")
st.markdown("Real-time case and referral monitoring across PHC gateways")
st.markdown("---")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_case_metrics_from_influxdb(
    client: InfluxDBConnection, days: int = 7, limit: int = 1000
) -> pd.DataFrame:
    """Query PHC metrics from InfluxDB for case data.

    Args:
        client: InfluxDBConnection instance
        days: Number of days to look back
        limit: Maximum records to return

    Returns:
        DataFrame with columns: timestamp, phc_id, district, state, cases, referrals
    """
    try:
        metrics = client.query_metrics(
            measurement="phc_metrics",
            filters={"metric_type": "cases"},
        )

        if not metrics:
            return pd.DataFrame()

        records = []
        for metric in metrics[:limit]:
            records.append(
                {
                    "timestamp": metric["time"],
                    "phc_id": metric["tags"].get("phc_id", "unknown"),
                    "district": metric["tags"].get("district", "unknown"),
                    "state": metric["tags"].get("state", "unknown"),
                    "cases": metric["value"],
                    "referrals": 0,  # Will be populated separately
                }
            )

        return pd.DataFrame(records)
    except Exception as e:
        st.warning(f"⚠️ InfluxDB connection error: {str(e)}")
        return generate_mock_case_data(days=days)


def generate_mock_case_data(days: int = 7) -> pd.DataFrame:
    """Generate realistic mock case data for testing.

    Args:
        days: Number of days of historical data

    Returns:
        DataFrame with mock case metrics
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
    phc_ids = [f"PHC{i:03d}" for i in range(1, 51)]

    records = []
    for day_offset in range(days):
        date = datetime.now() - timedelta(days=day_offset)
        for phc_id in phc_ids:
            district = districts[hash(phc_id) % len(districts)]
            cases = int(np.random.exponential(scale=10) + 5)
            referrals = int(np.random.poisson(lam=3))

            records.append(
                {
                    "timestamp": date,
                    "phc_id": phc_id,
                    "district": district,
                    "state": "Delhi",
                    "cases": cases,
                    "referrals": referrals,
                }
            )

    return pd.DataFrame(records)


# Sidebar filters
with st.sidebar:
    st.subheader("🔍 Filters")

    date_range = st.slider(
        "Date Range (days)",
        min_value=1,
        max_value=30,
        value=7,
        help="Historical data to display",
    )

    selected_districts = st.multiselect(
        "Districts",
        options=[
            "North Delhi",
            "South Delhi",
            "East Delhi",
            "West Delhi",
            "Central Delhi",
            "New Delhi",
        ],
        default=[
            "North Delhi",
            "South Delhi",
            "East Delhi",
            "West Delhi",
            "Central Delhi",
            "New Delhi",
        ],
    )

    min_cases_threshold = st.slider(
        "Minimum Cases Threshold",
        min_value=0,
        max_value=100,
        value=10,
        help="Highlight districts exceeding this threshold",
    )

# Load data
influxdb_client = InfluxDBConnection()
df = get_case_metrics_from_influxdb(influxdb_client, days=date_range)

# Filter by selected districts
if not df.empty:
    df = df[df["district"].isin(selected_districts)]
    df["timestamp"] = pd.to_datetime(df["timestamp"])

# Display key metrics
if not df.empty:
    total_cases = df["cases"].sum()
    total_referrals = df["referrals"].sum()
    unique_phcs = df["phc_id"].nunique()

    # Calculate trend (compare with previous period)
    if date_range > 7:
        prev_period = df[df["timestamp"] < (datetime.now() - timedelta(days=date_range / 2))]
        curr_period = df[
            df["timestamp"] >= (datetime.now() - timedelta(days=date_range / 2))
        ]

        prev_cases = prev_period["cases"].sum() if not prev_period.empty else total_cases
        curr_cases = curr_period["cases"].sum() if not curr_period.empty else total_cases

        trend = (
            ((curr_cases - prev_cases) / prev_cases * 100) if prev_cases > 0 else 0
        )
    else:
        trend = 0

    # Determine alert level
    if total_cases > 500:
        alert_level = "🔴 Critical"
        alert_color = "red"
    elif total_cases > 250:
        alert_level = "🟠 High"
        alert_color = "orange"
    elif total_cases > 100:
        alert_level = "🟡 Medium"
        alert_color = "yellow"
    else:
        alert_level = "🟢 Low"
        alert_color = "green"

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", f"{total_cases:,.0f}", f"{trend:+.1f}%")
    col2.metric("Total Referrals", f"{total_referrals:,.0f}", f"{total_referrals // max(total_cases, 1):.1f} per case")
    col3.metric("Active PHCs", unique_phcs)
    col4.metric("Alert Level", alert_level)

    st.markdown("---")

    # Cases by District - Bar Chart
    st.subheader("📊 Cases by District")
    cases_by_district = df.groupby("district").agg({"cases": "sum", "referrals": "sum"}).reset_index()
    cases_by_district = cases_by_district.sort_values("cases", ascending=False)

    fig_bar = px.bar(
        cases_by_district,
        x="district",
        y="cases",
        color="cases",
        color_continuous_scale="Reds",
        labels={"cases": "Case Count", "district": "District"},
        title="Total Cases by District (Last {} Days)".format(date_range),
        hover_data=["referrals"],
    )
    fig_bar.add_hline(
        y=min_cases_threshold,
        line_dash="dash",
        line_color="red",
        annotation_text="Alert Threshold",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # PHC-level heatmap (hotspots)
    st.subheader("🔥 Outbreak Hotspots - PHC Level")

    # Create heatmap data
    heatmap_data = df.groupby(["district", "phc_id"])["cases"].sum().reset_index()
    heatmap_pivot = heatmap_data.pivot_table(
        index="district", columns="phc_id", values="cases", fill_value=0
    )

    # Show top PHCs heatmap (limit to avoid huge matrix)
    top_phcs = df.groupby("phc_id")["cases"].sum().nlargest(15).index
    heatmap_subset = heatmap_data[heatmap_data["phc_id"].isin(top_phcs)]
    heatmap_pivot_subset = heatmap_subset.pivot_table(
        index="district", columns="phc_id", values="cases", fill_value=0
    )

    fig_heatmap = go.Figure(
        data=go.Heatmap(
            z=heatmap_pivot_subset.values,
            x=heatmap_pivot_subset.columns,
            y=heatmap_pivot_subset.index,
            colorscale="Reds",
            colorbar=dict(title="Cases"),
        )
    )
    fig_heatmap.update_layout(
        title="Case Hotspots - Top 15 PHCs",
        xaxis_title="PHC ID",
        yaxis_title="District",
        height=400,
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Time series trend
    st.subheader("📈 Cases Over Time")
    daily_trend = df.groupby(df["timestamp"].dt.date).agg({
        "cases": "sum",
        "referrals": "sum",
    }).reset_index()
    daily_trend.columns = ["Date", "Cases", "Referrals"]

    fig_trend = px.line(
        daily_trend,
        x="Date",
        y="Cases",
        title="Case Trend (Last {} Days)".format(date_range),
        markers=True,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # Alerts & Anomalies
    st.subheader("⚠️ Alert Summary")
    high_case_phcs = df.groupby("phc_id")["cases"].sum()
    high_case_phcs = high_case_phcs[high_case_phcs > min_cases_threshold].sort_values(ascending=False)

    if not high_case_phcs.empty:
        alert_df = pd.DataFrame(
            {
                "PHC ID": high_case_phcs.index,
                "Total Cases": high_case_phcs.values,
                "Status": ["🔴 HIGH"] * len(high_case_phcs),
            }
        )
        st.dataframe(alert_df, use_container_width=True)
    else:
        st.success("✅ No PHCs exceeding alert threshold")

    # Raw data table
    with st.expander("📋 View Raw Data"):
        st.dataframe(
            df.sort_values("timestamp", ascending=False),
            use_container_width=True,
        )

else:
    st.error("❌ No data available. Please check InfluxDB connection.")
    st.info("💡 Displaying mock data for demonstration purposes.")
    df = generate_mock_case_data(days=date_range)
    st.dataframe(df.head(20), use_container_width=True)

st.markdown("---")
st.markdown("Last updated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
