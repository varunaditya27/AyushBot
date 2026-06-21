"""Model Drift Analysis Dashboard Page - Model Performance & Privacy Tracking."""

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

from fl_server.model_registry import ModelRegistry

st.set_page_config(page_title="Model Drift Analysis", page_icon="📈", layout="wide")

# Configure page
st.title("📈 Model Drift Analysis Dashboard")
st.markdown("Monitor model performance trends and privacy budget consumption across FL rounds")
st.markdown("---")


@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_model_performance_from_registry(
    registry_path: str = "./models",
) -> pd.DataFrame:
    """Query model performance data from ModelRegistry.

    Args:
        registry_path: Path to model registry directory

    Returns:
        DataFrame with columns: version, round_num, num_clients, accuracy, loss,
                               epsilon_consumed, aggregation_strategy, timestamp
    """
    try:
        registry = ModelRegistry(local_path=registry_path, max_versions=100)
        versions = registry.list_versions()

        if not versions:
            return pd.DataFrame()

        records = []
        for version_info in versions:
            version, metadata, timestamp = version_info

            records.append(
                {
                    "version": version,
                    "round_num": metadata.get("round_num", 0),
                    "num_clients": metadata.get("num_clients", 0),
                    "accuracy": metadata.get("metrics", {}).get("accuracy", 0.0),
                    "loss": metadata.get("metrics", {}).get("loss", 0.0),
                    "epsilon_consumed": metadata.get("metrics", {}).get(
                        "epsilon_consumed", 0.0
                    ),
                    "aggregation_strategy": metadata.get("aggregation_strategy", "FedAvg"),
                    "model_size_bytes": metadata.get("model_size_bytes", 0),
                    "timestamp": timestamp,
                }
            )

        return pd.DataFrame(records)
    except Exception as e:
        st.warning(f"⚠️ ModelRegistry access error: {str(e)}")
        return generate_mock_model_performance_data()


def generate_mock_model_performance_data(num_rounds: int = 50) -> pd.DataFrame:
    """Generate realistic mock model performance data for testing.

    Args:
        num_rounds: Number of FL rounds to simulate

    Returns:
        DataFrame with model performance metrics
    """
    import numpy as np

    records = []
    epsilon_cumulative = 0
    accuracy = 0.65  # Starting accuracy

    for round_num in range(1, num_rounds + 1):
        # Accuracy improves with each round (with some noise)
        accuracy = min(
            0.99,
            accuracy + np.random.normal(0.008, 0.002),
        )

        # Loss decreases with accuracy improvement
        loss = 0.5 * (1 - accuracy) + np.random.normal(0, 0.01)
        loss = max(0, loss)

        # Epsilon consumption per round (tracked for DP budget)
        epsilon_round = np.random.uniform(0.01, 0.05)
        epsilon_cumulative += epsilon_round

        # Varying number of clients per round
        num_clients = max(
            5, int(np.random.normal(30, 8))
        )

        records.append(
            {
                "version": f"v_1_2026_05_31_{round_num:02d}0000_000000",
                "round_num": round_num,
                "num_clients": num_clients,
                "accuracy": accuracy,
                "loss": loss,
                "epsilon_consumed": epsilon_cumulative,
                "aggregation_strategy": "FedAvg" if round_num < 26 else "FedProx",
                "model_size_bytes": int(1e6 + np.random.normal(0, 1e4)),
                "timestamp": datetime.now() - timedelta(hours=50 - round_num),
            }
        )

    return pd.DataFrame(records)


# Sidebar configuration
with st.sidebar:
    st.subheader("🔍 Filters & Controls")

    min_round = st.slider(
        "Minimum Round",
        min_value=1,
        max_value=100,
        value=1,
        help="Start from this round",
    )

    max_round = st.slider(
        "Maximum Round",
        min_value=1,
        max_value=100,
        value=50,
        help="End at this round",
    )

    metric_to_plot = st.selectbox(
        "Primary Metric",
        options=["Accuracy", "Loss", "Epsilon"],
        help="Choose metric for trend visualization",
    )

    epsilon_budget = st.number_input(
        "Total DP Epsilon Budget",
        min_value=0.1,
        max_value=10.0,
        value=1.0,
        step=0.1,
        help="Total differential privacy budget",
    )

# Load data
df = get_model_performance_from_registry()

# Filter by round range
if not df.empty:
    df = df[(df["round_num"] >= min_round) & (df["round_num"] <= max_round)]

if not df.empty:
    # Calculate metrics
    latest_accuracy = df.iloc[-1]["accuracy"] if not df.empty else 0
    latest_loss = df.iloc[-1]["loss"] if not df.empty else 0
    total_epsilon = df.iloc[-1]["epsilon_consumed"] if not df.empty else 0
    epsilon_remaining = max(0, epsilon_budget - total_epsilon)
    epsilon_pct = (total_epsilon / epsilon_budget * 100) if epsilon_budget > 0 else 0

    # Accuracy improvement
    if len(df) > 1:
        accuracy_improvement = df.iloc[-1]["accuracy"] - df.iloc[0]["accuracy"]
    else:
        accuracy_improvement = 0

    # Loss improvement
    if len(df) > 1:
        loss_improvement = df.iloc[0]["loss"] - df.iloc[-1]["loss"]
    else:
        loss_improvement = 0

    # Display key metrics
    st.subheader("📊 Model Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Latest Accuracy", f"{latest_accuracy:.3f}", f"{accuracy_improvement:+.3f}")
    col2.metric("Latest Loss", f"{latest_loss:.3f}", f"{-loss_improvement:+.3f}")
    col3.metric("DP Epsilon Used", f"{total_epsilon:.2f}/{epsilon_budget:.2f}", f"{epsilon_pct:.0f}%")
    col4.metric("Rounds Completed", len(df), f"Avg {df['num_clients'].mean():.0f} clients/round")

    st.markdown("---")

    # Privacy budget consumption progress bar
    st.subheader("🔐 Differential Privacy Budget")
    col1, col2 = st.columns([4, 1])

    with col1:
        progress = min(1.0, total_epsilon / epsilon_budget) if epsilon_budget > 0 else 0
        st.progress(progress, text=f"{epsilon_pct:.1f}% budget consumed")

    with col2:
        if epsilon_pct > 90:
            st.error(f"⚠️ {epsilon_remaining:.2f} remaining")
        elif epsilon_pct > 75:
            st.warning(f"⚠️ {epsilon_remaining:.2f} remaining")
        else:
            st.info(f"✅ {epsilon_remaining:.2f} remaining")

    st.markdown("---")

    # Primary metric trend
    st.subheader(f"📈 {metric_to_plot} Trend Over Rounds")

    if metric_to_plot == "Accuracy":
        fig_trend = px.line(
            df,
            x="round_num",
            y="accuracy",
            title="Model Accuracy Convergence",
            markers=True,
            labels={"round_num": "Round", "accuracy": "Accuracy"},
            line_shape="linear",
        )
        fig_trend.add_hline(
            y=0.95,
            line_dash="dash",
            line_color="green",
            annotation_text="Target Accuracy (0.95)",
        )

    elif metric_to_plot == "Loss":
        fig_trend = px.line(
            df,
            x="round_num",
            y="loss",
            title="Model Loss Convergence",
            markers=True,
            labels={"round_num": "Round", "loss": "Loss"},
            line_shape="linear",
        )
        fig_trend.add_hline(
            y=0.05,
            line_dash="dash",
            line_color="green",
            annotation_text="Target Loss (0.05)",
        )

    else:  # Epsilon
        fig_trend = px.line(
            df,
            x="round_num",
            y="epsilon_consumed",
            title="Cumulative DP Epsilon Consumption",
            markers=True,
            labels={"round_num": "Round", "epsilon_consumed": "Cumulative Epsilon"},
            line_shape="linear",
        )
        fig_trend.add_hline(
            y=epsilon_budget,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Budget Limit ({epsilon_budget})",
        )

    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # Dual-axis: Accuracy vs Loss
    st.subheader("📊 Accuracy vs Loss (Dual Axis)")

    fig_dual = go.Figure()

    # Accuracy
    fig_dual.add_trace(
        go.Scatter(
            x=df["round_num"],
            y=df["accuracy"],
            mode="lines+markers",
            name="Accuracy",
            yaxis="y1",
            line=dict(color="green"),
        )
    )

    # Loss
    fig_dual.add_trace(
        go.Scatter(
            x=df["round_num"],
            y=df["loss"],
            mode="lines+markers",
            name="Loss",
            yaxis="y2",
            line=dict(color="red"),
        )
    )

    fig_dual.update_layout(
        title="Model Convergence: Accuracy vs Loss",
        xaxis=dict(title="Round"),
        yaxis=dict(title="Accuracy", side="left"),
        yaxis2=dict(title="Loss", overlaying="y", side="right"),
        hovermode="x unified",
        height=500,
    )

    st.plotly_chart(fig_dual, use_container_width=True)

    st.markdown("---")

    # Aggregation strategy and client participation
    st.subheader("📊 Training Dynamics")
    col1, col2 = st.columns(2)

    with col1:
        # Strategy distribution
        strategy_counts = df["aggregation_strategy"].value_counts().reset_index()
        strategy_counts.columns = ["strategy", "count"]

        fig_strategy = px.pie(
            strategy_counts,
            names="strategy",
            values="count",
            title="Aggregation Strategy Distribution",
        )
        st.plotly_chart(fig_strategy, use_container_width=True)

    with col2:
        # Client participation over rounds
        fig_clients = px.line(
            df,
            x="round_num",
            y="num_clients",
            title="Client Participation per Round",
            markers=True,
            labels={"round_num": "Round", "num_clients": "Number of Clients"},
        )
        st.plotly_chart(fig_clients, use_container_width=True)

    st.markdown("---")

    # Model version selector and details
    st.subheader("🔍 Model Version Details")

    selected_version = st.selectbox(
        "Select Model Version",
        options=df["version"].tolist(),
        index=len(df) - 1,  # Select latest by default
    )

    version_data = df[df["version"] == selected_version].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Round", int(version_data["round_num"]))
    col2.metric("Clients", int(version_data["num_clients"]))
    col3.metric("Model Size", f"{version_data['model_size_bytes'] / 1e6:.2f} MB")

    col1, col2, col3 = st.columns(3)
    col1.metric("Accuracy", f"{version_data['accuracy']:.4f}")
    col2.metric("Loss", f"{version_data['loss']:.4f}")
    col3.metric("Strategy", version_data["aggregation_strategy"])

    # Download model button (simulated)
    if st.button(f"📥 Download {selected_version}"):
        st.success(f"✅ Model {selected_version} ready for download")
        st.info("In production: Model bytes would be streamed here")

    st.markdown("---")

    # Raw metrics table
    with st.expander("📋 View All Metrics"):
        display_df = df[
            [
                "version",
                "round_num",
                "num_clients",
                "accuracy",
                "loss",
                "epsilon_consumed",
                "aggregation_strategy",
                "timestamp",
            ]
        ].copy()
        display_df["accuracy"] = display_df["accuracy"].apply(lambda x: f"{x:.4f}")
        display_df["loss"] = display_df["loss"].apply(lambda x: f"{x:.4f}")
        display_df["epsilon_consumed"] = display_df["epsilon_consumed"].apply(
            lambda x: f"{x:.3f}"
        )

        st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.error("❌ No model data available.")
    st.info("💡 Displaying mock data for demonstration purposes.")
    df = generate_mock_model_performance_data()
    st.dataframe(df.head(20), use_container_width=True)

st.markdown("---")
st.markdown("Last updated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
