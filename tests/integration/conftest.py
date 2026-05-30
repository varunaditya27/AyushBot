"""Pytest configuration and fixtures for integration tests."""

import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock
from flwr.common import FitRes, Parameters


@pytest.fixture
def tmp_models_dir(tmp_path):
    """Create a temporary models directory."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    return models_dir


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a temporary config.yaml file."""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
fl:
  port: 8080
  strategy: FedAvg
  min_clients: 2
  rounds: 3
  timeout: 300

privacy:
  epsilon: 1.0
  delta: 1e-6
  gradient_clipping:
    max_norm: 1.0
  noise_injection:
    enabled: true

model_storage:
  local_path: {}
  max_versions: 10
""".format(str(tmp_path / "models")))
    return config_file


@pytest.fixture
def mock_gradient():
    """Create a mock gradient array."""
    return np.random.randn(10)


@pytest.fixture
def mock_client_fit_result():
    """Create a mock FitRes for FL client."""
    def _create_fit_result(weights=None, num_examples=100, metrics=None):
        if weights is None:
            weights = [np.random.randn(10)]
        if metrics is None:
            metrics = {"loss": 0.5}
        
        parameters = Parameters(tensors=weights, tensor_type="numpy")
        return FitRes(
            parameters=parameters,
            num_examples=num_examples,
            metrics=metrics,
        )
    
    return _create_fit_result


@pytest.fixture
def mock_client_list():
    """Create a list of mock clients."""
    def _create_clients(num_clients=3, num_examples_base=100):
        clients = []
        for i in range(num_clients):
            weights = [np.random.randn(10)]
            parameters = Parameters(tensors=weights, tensor_type="numpy")
            fit_res = FitRes(
                parameters=parameters,
                num_examples=num_examples_base + i * 50,
                metrics={"loss": 0.5 - i * 0.05},
            )
            clients.append((MagicMock(), fit_res))
        return clients
    
    return _create_clients
