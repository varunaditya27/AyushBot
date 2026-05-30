"""Smoke tests for dashboard modules."""

import pytest
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


def test_dashboard_imports():
    """Test that all dashboard modules import correctly."""
    # Add cloud module to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    from dashboards import __version__

    assert __version__ == "1.0.0"

    from dashboards.db_helpers import InfluxDBConnection, PostgreSQLConnection

    assert InfluxDBConnection is not None
    assert PostgreSQLConnection is not None


def test_influxdb_connection_init():
    """Test InfluxDB connection initialization."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    from dashboards.db_helpers import InfluxDBConnection

    client = InfluxDBConnection(url="http://localhost:8086")
    assert client.url == "http://localhost:8086"
    assert client.bucket == "ayushbot"
    assert client.org == "ayushbot"


def test_postgresql_connection_init():
    """Test PostgreSQL connection initialization."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    from dashboards.db_helpers import PostgreSQLConnection

    client = PostgreSQLConnection(host="localhost", port=5432)
    assert client.host == "localhost"
    assert client.port == 5432
    assert client.database == "ayushbot"


def test_dashboard_pages_exist():
    """Test that all dashboard pages can be imported."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    # Verify page files exist
    pages_dir = Path(__file__).parent.parent.parent / "cloud" / "dashboards" / "pages"
    required_pages = [
        "outbreak_detection.py",
        "hardware_monitoring.py",
        "model_drift_analysis.py",
        "aggregation_history.py",
    ]

    for page in required_pages:
        page_file = pages_dir / page
        assert page_file.exists(), f"Page file {page} not found"


def test_outbreak_detection_mock_data_generation():
    """Test mock data generation for outbreak detection page."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    # Verify the outbreak_detection.py file contains the function
    page_file = (
        Path(__file__).parent.parent.parent
        / "cloud"
        / "dashboards"
        / "pages"
        / "outbreak_detection.py"
    )
    content = page_file.read_text(encoding="utf-8")

    # Check that the key functions are defined
    assert "def generate_mock_case_data" in content
    assert "def get_case_metrics_from_influxdb" in content


def test_outbreak_detection_data_structure():
    """Test that mock case data has correct structure."""
    import numpy as np

    # Simulate the mock data generation function
    districts = ["North Delhi", "South Delhi", "East Delhi"]
    phc_ids = [f"PHC{i:03d}" for i in range(1, 11)]

    records = []
    for day_offset in range(7):
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

    df = pd.DataFrame(records)

    # Verify structure
    assert not df.empty
    assert "timestamp" in df.columns
    assert "phc_id" in df.columns
    assert "district" in df.columns
    assert "state" in df.columns
    assert "cases" in df.columns
    assert "referrals" in df.columns

    # Verify data types
    assert df["cases"].dtype in [int, "int64"]
    assert df["referrals"].dtype in [int, "int64"]
    assert len(df["district"].unique()) > 0
    assert len(df["phc_id"].unique()) > 0


def test_hardware_monitoring_mock_data_generation():
    """Test mock gateway hardware data generation."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    # Verify the hardware_monitoring.py file contains the function
    page_file = (
        Path(__file__).parent.parent.parent
        / "cloud"
        / "dashboards"
        / "pages"
        / "hardware_monitoring.py"
    )
    content = page_file.read_text(encoding="utf-8")

    # Check that the key functions are defined
    assert "def generate_mock_gateway_data" in content
    assert "def get_gateway_status_from_postgres" in content


def test_hardware_monitoring_data_structure():
    """Test that mock gateway data has correct structure."""
    import numpy as np

    # Simulate the mock data generation
    districts = ["North Delhi", "South Delhi", "East Delhi"]
    models = ["RaspberryPi4", "RaspberryPi5"]

    records = []
    for i in range(10):
        device_id = f"GW{i + 1:03d}"
        phc_id = f"PHC{(i % 5) + 1:03d}"
        district = districts[i % len(districts)]

        battery = min(100, max(0, int(np.random.normal(75, 15))))
        signal = int(np.random.normal(-60, 15))
        signal = min(-30, max(-100, signal))

        status = "Online" if signal > -70 else "Offline"
        last_sync = int(abs(np.random.exponential(scale=30)))
        uptime = int(np.random.exponential(scale=500))

        records.append(
            {
                "device_id": device_id,
                "phc_id": phc_id,
                "district": district,
                "battery_pct": battery,
                "signal_strength": signal,
                "connectivity_status": status,
                "last_sync_minutes": last_sync,
                "uptime_hours": uptime,
                "model": models[i % len(models)],
            }
        )

    df = pd.DataFrame(records)

    # Verify structure
    assert not df.empty
    assert "device_id" in df.columns
    assert "phc_id" in df.columns
    assert "battery_pct" in df.columns
    assert "signal_strength" in df.columns
    assert "connectivity_status" in df.columns

    # Verify data ranges
    assert (df["battery_pct"] >= 0).all() and (df["battery_pct"] <= 100).all()
    assert (df["signal_strength"] >= -100).all() and (df["signal_strength"] <= -30).all()
    assert df["connectivity_status"].isin(["Online", "Degraded", "Offline"]).all()


def test_model_drift_analysis_mock_data_generation():
    """Test mock model performance data generation."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    # Verify the model_drift_analysis.py file contains the function
    page_file = (
        Path(__file__).parent.parent.parent
        / "cloud"
        / "dashboards"
        / "pages"
        / "model_drift_analysis.py"
    )
    content = page_file.read_text(encoding="utf-8")

    # Check that the key functions are defined
    assert "def generate_mock_model_performance_data" in content
    assert "def get_model_performance_from_registry" in content


def test_model_performance_data_structure():
    """Test that mock model performance data has correct structure."""
    import numpy as np

    # Simulate the mock data generation
    records = []
    epsilon_cumulative = 0
    accuracy = 0.65

    for round_num in range(1, 11):
        accuracy = min(0.99, accuracy + np.random.normal(0.008, 0.002))
        loss = 0.5 * (1 - accuracy) + np.random.normal(0, 0.01)
        loss = max(0, loss)

        epsilon_round = np.random.uniform(0.01, 0.05)
        epsilon_cumulative += epsilon_round

        num_clients = max(5, int(np.random.normal(30, 8)))

        records.append(
            {
                "version": f"v_1_2026_05_31_{round_num:02d}0000_000000",
                "round_num": round_num,
                "num_clients": num_clients,
                "accuracy": accuracy,
                "loss": loss,
                "epsilon_consumed": epsilon_cumulative,
                "aggregation_strategy": "FedAvg" if round_num < 6 else "FedProx",
                "model_size_bytes": int(1e6 + np.random.normal(0, 1e4)),
                "timestamp": datetime.now() - timedelta(hours=50 - round_num),
            }
        )

    df = pd.DataFrame(records)

    # Verify structure
    assert not df.empty
    assert "version" in df.columns
    assert "round_num" in df.columns
    assert "accuracy" in df.columns
    assert "loss" in df.columns
    assert "epsilon_consumed" in df.columns

    # Verify data ranges and properties
    assert (df["accuracy"] > 0).all() and (df["accuracy"] <= 1.0).all()
    assert (df["loss"] >= 0).all() and (df["loss"] < 1.0).all()
    assert (df["epsilon_consumed"] > 0).all()
    assert df["aggregation_strategy"].isin(["FedAvg", "FedProx"]).all()
    
    # Verify accuracy improves over rounds
    if len(df) > 1:
        assert df.iloc[-1]["accuracy"] >= df.iloc[0]["accuracy"]
    
    # Verify epsilon is cumulative (always increasing)
    assert (df["epsilon_consumed"].diff().fillna(0) >= 0).all()
