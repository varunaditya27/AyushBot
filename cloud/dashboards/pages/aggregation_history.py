"""Aggregation History Dashboard Page - FL Training Round Timeline."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

st.set_page_config(page_title="Aggregation History", page_icon="⏱️", layout="wide")

# Configure page
st.title("⏱️ Aggregation History Dashboard")
st.markdown("Monitor FL training rounds, aggregation timing, and client participation history")
st.markdown("---")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_aggregation_history_from_registry(
    registry_path: str = "./models",
) -> pd.DataFrame:
    """Query aggregation history from ModelRegistry.

    Args:
        registry_path: Path to model registry directory

    Returns:
        DataFrame with round metadata and timing information
    """
    try:
        from fl_server.model_registry import ModelRegistry

        registry = ModelRegistry(local_path=registry_path, max_versions=100)
        versions = registry.list_versions()

        if not versions:
            return pd.DataFrame()

        records = []
        for version_info in versions:
            version, metadata, timestamp = version_info

            records.append(
                {
                    "round_num": metadata.get("round_num", 0),
                    "num_clients": metadata.get("num_clients", 0),
                    "aggregation_strategy": metadata.get("aggregation_strategy", "FedAvg"),
                    "status": "Success",  # Phase 2 only saves successful rounds
                    "timestamp": timestamp,
                    "model_size_bytes": metadata.get("model_size_bytes", 0),
                    "metrics": metadata.get("metrics", {}),
                }
            )

        return pd.DataFrame(records)
    except Exception as e:
        st.warning(f"⚠️ ModelRegistry access error: {str(e)}")
        return generate_mock_aggregation_history()


def generate_mock_aggregation_history(num_rounds: int = 50) -> pd.DataFrame:
    """Generate realistic mock aggregation history data.

    Args:
        num_rounds: Number of FL rounds to simulate

    Returns:
        DataFrame with aggregation round history
    """
    import numpy as np

    records = []
    base_time = datetime.now() - timedelta(hours=50)

    for round_num in range(1, num_rounds + 1):
        # Aggregation time (improves as rounds progress)
        base_agg_time = 5.0 - (round_num / num_rounds) * 1.5
        agg_time = max(2.0, base_agg_time + np.random.normal(0, 0.5))

        # Number of clients (varies per round)
        num_clients = max(5, int(np.random.normal(30, 8)))

        # Total samples aggregated
        samples_per_client = np.random.randint(100, 500)
        total_samples = num_clients * samples_per_client

        # Gradient norm (for DP clipping validation)
        grad_norm = np.random.exponential(scale=1.5)

        # Communication rounds (inner iterations)
        comm_rounds = np.random.randint(3, 10)

        # Status: mostly success, occasional failures
        status = "Success" if np.random.random() > 0.02 else "Failed"

        round_time = base_time + timedelta(minutes=5 * (round_num - 1))

        records.append(
            {
                "round_num": round_num,
                "num_clients": num_clients,
                "aggregation_strategy": "FedAvg" if round_num < 26 else "FedProx",
                "status": status,
                "timestamp": round_time,
                "agg_time_sec": agg_time,
                "total_samples": total_samples,
                "gradient_norm": grad_norm,
                "comm_rounds": comm_rounds,
                "model_size_bytes": int(1e6 + np.random.normal(0, 1e4)),
            }
        )

    return pd.DataFrame(records)


# Sidebar configuration
with st.sidebar:
    st.subheader("🔍 Filters & Controls")

    status_filter = st.multiselect(
        "Round Status",
        options=["Success", "Failed"],
        default=["Success"],
        help="Filter by aggregation result",
    )

    strategy_filter = st.multiselect(
        "Aggregation Strategy",
        options=["FedAvg", "FedProx"],
        default=["FedAvg", "FedProx"],
        help="Filter by strategy used",
    )

    min_clients = st.slider(
        "Minimum Clients",
        min_value=1,
        max_value=100,
        value=5,
        help="Minimum clients per round",
    )

    time_window = st.selectbox(
        "Time Window",
        options=["Last 24h", "Last 7d", "All"],
        help="Filter by time range",
    )

# Load data
df = generate_mock_aggregation_history()

# Apply filters
if not df.empty:
    df = df[
        (df["status"].isin(status_filter))
        & (df["aggregation_strategy"].isin(strategy_filter))
        & (df["num_clients"] >= min_clients)
    ]

if not df.empty:
    # Calculate summary metrics
    total_rounds = len(df)
    success_count = (df["status"] == "Success").sum()
    success_rate = (success_count / total_rounds * 100) if total_rounds > 0 else 0
    avg_clients = df["num_clients"].mean()
    avg_agg_time = df["agg_time_sec"].mean()
    total_samples = df["total_samples"].sum()

    # Display summary metrics
    st.subheader("📊 Aggregation Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total Rounds", total_rounds)
    col2.metric("Success Rate", f"{success_rate:.1f}%")
    col3.metric("Avg Clients/Round", f"{avg_clients:.0f}")
    col4.metric("Avg Agg Time", f"{avg_agg_time:.2f}s")
    col5.metric("Total Samples", f"{total_samples:,}")

    st.markdown("---")

    # Round status distribution
    st.subheader("📈 Round Timeline & Status")

    fig_timeline = px.timeline(
        df.sort_values("round_num"),
        x_start="timestamp",
        x_end="timestamp",
        y="round_num",
        color="status",
        hover_data=["num_clients", "agg_time_sec", "aggregation_strategy"],
        title="Aggregation Round Timeline",
        color_discrete_map={"Success": "green", "Failed": "red"},
        height=600,
    )

    fig_timeline.update_yaxes(title_text="Round Number")
    fig_timeline.update_xaxes(title_text="Timestamp")

    st.plotly_chart(fig_timeline, use_container_width=True)

    st.markdown("---")

    # Aggregation time analysis
    st.subheader("⏱️ Aggregation Time Analysis")
    col1, col2 = st.columns(2)

    with col1:
        # Line chart: Agg time per round
        fig_time = px.line(
            df.sort_values("round_num"),
            x="round_num",
            y="agg_time_sec",
            title="Aggregation Time per Round",
            markers=True,
            labels={"round_num": "Round", "agg_time_sec": "Time (seconds)"},
        )
        fig_time.add_hline(
            y=avg_agg_time,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Avg: {avg_agg_time:.2f}s",
        )
        st.plotly_chart(fig_time, use_container_width=True)

    with col2:
        # Histogram: Distribution of agg times
        fig_hist = px.histogram(
            df,
            x="agg_time_sec",
            nbins=20,
            title="Aggregation Time Distribution",
            labels={"agg_time_sec": "Time (seconds)", "count": "Frequency"},
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.markdown("---")

    # Client participation analysis
    st.subheader("👥 Client Participation")
    col1, col2 = st.columns(2)

    with col1:
        # Line: Clients per round
        fig_clients = px.line(
            df.sort_values("round_num"),
            x="round_num",
            y="num_clients",
            title="Clients per Round",
            markers=True,
            labels={"round_num": "Round", "num_clients": "Number of Clients"},
        )
        fig_clients.add_hline(
            y=avg_clients,
            line_dash="dash",
            line_color="orange",
            annotation_text=f"Avg: {avg_clients:.0f}",
        )
        st.plotly_chart(fig_clients, use_container_width=True)

    with col2:
        # Total samples aggregated per round
        fig_samples = px.bar(
            df.sort_values("round_num"),
            x="round_num",
            y="total_samples",
            title="Total Samples per Round",
            labels={"round_num": "Round", "total_samples": "Samples"},
        )
        st.plotly_chart(fig_samples, use_container_width=True)

    st.markdown("---")

    # Strategy and gradient norm analysis
    st.subheader("🔧 Training Dynamics")
    col1, col2 = st.columns(2)

    with col1:
        # Strategy distribution pie
        strategy_counts = df["aggregation_strategy"].value_counts().reset_index()
        strategy_counts.columns = ["strategy", "count"]

        fig_strategy = px.pie(
            strategy_counts,
            names="strategy",
            values="count",
            title="Strategy Distribution",
        )
        st.plotly_chart(fig_strategy, use_container_width=True)

    with col2:
        # Gradient norm per round (DP clipping indicator)
        fig_grad = px.scatter(
            df.sort_values("round_num"),
            x="round_num",
            y="gradient_norm",
            title="Gradient Norm per Round",
            size="num_clients",
            color="status",
            color_discrete_map={"Success": "green", "Failed": "red"},
        )
        st.plotly_chart(fig_grad, use_container_width=True)

    st.markdown("---")

    # Round details table
    st.subheader("🔍 Round Details")

    display_df = df.sort_values("round_num", ascending=False)[
        [
            "round_num",
            "num_clients",
            "aggregation_strategy",
            "status",
            "agg_time_sec",
            "total_samples",
            "gradient_norm",
            "comm_rounds",
        ]
    ].copy()

    display_df["agg_time_sec"] = display_df["agg_time_sec"].apply(lambda x: f"{x:.2f}s")
    display_df["gradient_norm"] = display_df["gradient_norm"].apply(lambda x: f"{x:.3f}")
    display_df.columns = [
        "Round",
        "Clients",
        "Strategy",
        "Status",
        "Agg Time",
        "Samples",
        "Grad Norm",
        "Comm Rounds",
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Export raw data
    with st.expander("📋 View Raw Data"):
        raw_df = df.sort_values("round_num", ascending=False).copy()
        raw_df["timestamp"] = raw_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")

        st.dataframe(raw_df, use_container_width=True, hide_index=True)

else:
    st.error("❌ No aggregation history available.")
    st.info("💡 Displaying mock data for demonstration purposes.")
    df = generate_mock_aggregation_history()
    st.dataframe(df.head(20), use_container_width=True)

st.markdown("---")
st.markdown("Last updated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

st.markdown("---")
st.markdown("Last updated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
