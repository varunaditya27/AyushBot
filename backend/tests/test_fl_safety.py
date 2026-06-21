from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from backend.config import clear_settings_cache, load_settings
from backend.fl import fl_client
from backend.security.transport import validate_production_security


@pytest.fixture(autouse=True)
def _clear_config():
	clear_settings_cache()
	yield
	clear_settings_cache()


def test_fl_client_start_disabled_by_default():
	with pytest.raises(RuntimeError, match="disabled"):
		fl_client.start_client()


def test_fit_rejects_training_when_disabled():
	cfg = fl_client.FLConfig(
		enabled=False,
		training_enabled=False,
		update_representation="not_implemented",
		server_address="127.0.0.1:8080",
		model_path="",
		train_data_path="",
		eval_data_path="",
		local_epochs=1,
		learning_rate=0.1,
		min_batch_size=1,
		dp_epsilon=1.0,
		dp_delta=1e-6,
		dp_max_grad_norm=1.0,
	)
	client = fl_client.XGBoostFlowerClient(cfg)

	with pytest.raises(RuntimeError, match="training is disabled"):
		client.fit([np.array([1, 2, 3], dtype=np.uint8)], {})


def test_fit_rejects_missing_structured_update_representation():
	cfg = fl_client.FLConfig(
		enabled=True,
		training_enabled=True,
		update_representation="not_implemented",
		server_address="127.0.0.1:8080",
		model_path="",
		train_data_path="",
		eval_data_path="",
		local_epochs=1,
		learning_rate=0.1,
		min_batch_size=1,
		dp_epsilon=1.0,
		dp_delta=1e-6,
		dp_max_grad_norm=1.0,
	)
	client = fl_client.XGBoostFlowerClient(cfg)

	with pytest.raises(NotImplementedError, match="structured update representation"):
		client.fit([np.array([1, 2, 3], dtype=np.uint8)], {})


def test_evaluate_path_is_testable_with_mocked_xgboost(tmp_path, monkeypatch):
	eval_data = tmp_path / "eval.npz"
	np.savez(
		eval_data,
		X=np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
		y=np.array([0, 1], dtype=np.int64),
	)

	class _Booster:
		def predict(self, _dtest):
			return np.array([[0.9, 0.1], [0.2, 0.8]])

	cfg = fl_client.FLConfig(
		enabled=False,
		training_enabled=False,
		update_representation="not_implemented",
		server_address="127.0.0.1:8080",
		model_path="",
		train_data_path="",
		eval_data_path=str(eval_data),
		local_epochs=1,
		learning_rate=0.1,
		min_batch_size=1,
		dp_epsilon=1.0,
		dp_delta=1e-6,
		dp_max_grad_norm=1.0,
	)
	client = fl_client.XGBoostFlowerClient(cfg)
	monkeypatch.setattr(client, "_load_model", lambda _params: _Booster())
	monkeypatch.setattr(
		fl_client,
		"_xgboost",
		lambda: SimpleNamespace(DMatrix=lambda X, label: {"X": X, "label": label}),
	)

	loss, count, metrics = client.evaluate([np.array([1], dtype=np.uint8)], {})

	assert loss == 0.0
	assert count == 2
	assert metrics["accuracy"] == 1.0


def test_production_rejects_enabled_fl(tmp_path, monkeypatch):
	from backend.security import transport

	monkeypatch.setattr(
		transport, "validate_auth_key_configuration", lambda _settings: None
	)
	cert = tmp_path / "cert.pem"
	cert.write_text("synthetic certificate placeholder", encoding="utf-8")
	config = tmp_path / "production.yaml"
	config.write_text(
		f"""
environment: production
api:
  cors_origins: ["https://demo.local"]
  tls_cert_path: {cert}
  tls_key_path: {cert}
mqtt:
  enabled: true
  tls_enabled: true
  port: 8883
  ca_cert_path: {cert}
  client_cert_path: {cert}
  client_key_path: {cert}
fl:
  enabled: true
triage_model:
  enabled: false
""",
		encoding="utf-8",
	)
	settings = load_settings(config, create_dirs=False)

	with pytest.raises(RuntimeError, match="FL training is incomplete"):
		validate_production_security(settings)
