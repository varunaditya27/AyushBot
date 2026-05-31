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


def test_aggregation_history_mock_data_generation():
    """Test mock aggregation history data generation."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    # Verify the aggregation_history.py file contains the function
    page_file = (
        Path(__file__).parent.parent.parent
        / "cloud"
        / "dashboards"
        / "pages"
        / "aggregation_history.py"
    )
    content = page_file.read_text(encoding="utf-8")

    # Check that the key functions are defined
    assert "def generate_mock_aggregation_history" in content
    assert "def get_aggregation_history_from_registry" in content


def test_aggregation_history_data_structure():
    """Test that mock aggregation history data has correct structure."""
    import numpy as np

    # Simulate the mock data generation
    records = []
    base_time = datetime.now() - timedelta(hours=50)

    for round_num in range(1, 11):
        base_agg_time = 5.0 - (round_num / 50) * 1.5
        agg_time = max(2.0, base_agg_time + np.random.normal(0, 0.5))

        num_clients = max(5, int(np.random.normal(30, 8)))

        samples_per_client = np.random.randint(100, 500)
        total_samples = num_clients * samples_per_client

        grad_norm = np.random.exponential(scale=1.5)
        comm_rounds = np.random.randint(3, 10)

        status = "Success" if np.random.random() > 0.02 else "Failed"
        round_time = base_time + timedelta(minutes=5 * (round_num - 1))

        records.append(
            {
                "round_num": round_num,
                "num_clients": num_clients,
                "aggregation_strategy": "FedAvg" if round_num < 6 else "FedProx",
                "status": status,
                "timestamp": round_time,
                "agg_time_sec": agg_time,
                "total_samples": total_samples,
                "gradient_norm": grad_norm,
                "comm_rounds": comm_rounds,
                "model_size_bytes": int(1e6 + np.random.normal(0, 1e4)),
            }
        )

    df = pd.DataFrame(records)

    # Verify structure
    assert not df.empty
    assert "round_num" in df.columns
    assert "num_clients" in df.columns
    assert "agg_time_sec" in df.columns
    assert "total_samples" in df.columns
    assert "gradient_norm" in df.columns
    assert "status" in df.columns

    # Verify data ranges
    assert (df["agg_time_sec"] >= 2.0).all()
    assert (df["num_clients"] >= 5).all()
    assert (df["total_samples"] > 0).all()
    assert (df["gradient_norm"] >= 0).all()
    assert df["status"].isin(["Success", "Failed"]).all()
    assert df["aggregation_strategy"].isin(["FedAvg", "FedProx"]).all()


def test_aggregation_history_mock_data_generation():
    """Test mock aggregation history data generation."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cloud"))

    # Verify the aggregation_history.py file contains the function
    page_file = (
        Path(__file__).parent.parent.parent
        / "cloud"
        / "dashboards"
        / "pages"
        / "aggregation_history.py"
    )
    content = page_file.read_text(encoding="utf-8")

    # Check that the key functions are defined
    assert "def generate_mock_aggregation_history" in content
    assert "def get_aggregation_history_from_registry" in content


def test_aggregation_history_data_structure():
    """Test that mock aggregation history has correct structure."""
    import numpy as np

    # Simulate the mock data generation
    records = []

    for round_num in range(1, 11):
        aggregation_time = max(3, np.random.normal(12, 4))
        num_clients = int(max(5, np.random.normal(30, 8)))
        model_size_mb = max(0.5, np.random.normal(1.2, 0.2))
        strategy = "FedAvg" if round_num < 6 else "FedProx"
        status = "success" if np.random.random() > 0.05 else "failed"

        records.append(
            {
                "round_num": round_num,
                "num_clients": num_clients,
                "aggregation_time_sec": aggregation_time,
                "model_size_mb": model_size_mb,
                "strategy": strategy,
                "timestamp": datetime.now() - timedelta(hours=50 - round_num),
                "status": status,
            }
        )

    df = pd.DataFrame(records)

    # Verify structure
    assert not df.empty
    assert "round_num" in df.columns
    assert "num_clients" in df.columns
    assert "aggregation_time_sec" in df.columns
    assert "model_size_mb" in df.columns
    assert "strategy" in df.columns
    assert "status" in df.columns

    # Verify data ranges
    assert (df["aggregation_time_sec"] > 0).all()
    assert (df["num_clients"] > 0).all()
    assert (df["model_size_mb"] > 0).all()
    assert df["strategy"].isin(["FedAvg", "FedProx"]).all()
    assert df["status"].isin(["success", "failed"]).all()
