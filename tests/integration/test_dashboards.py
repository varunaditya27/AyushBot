"""Smoke tests for dashboard modules."""

import pytest
import sys
from pathlib import Path


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
