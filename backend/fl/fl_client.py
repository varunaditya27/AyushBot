"""AyushBot Backend — Flower FL client for XGBoost triage model."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import flwr as fl
import numpy as np
import xgboost as xgb
import yaml

from backend.fl.privacy import apply_dp

logger = logging.getLogger(__name__)


@dataclass
class FLConfig:
    server_address: str
    model_path: str
    train_data_path: str
    eval_data_path: str
    local_epochs: int
    learning_rate: float
    min_batch_size: int
    dp_epsilon: float
    dp_delta: float
    dp_max_grad_norm: float


def _load_config() -> Dict[str, Any]:
    config_path = os.getenv("AYUSHBOT_CONFIG") or os.path.join(
        os.path.dirname(__file__), "..", "config.yaml"
    )
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to load config: %s", exc)
        return {}


def _build_config() -> FLConfig:
    config = _load_config()
    fl_cfg = config.get("fl", {}) if isinstance(config, dict) else {}
    server_address = os.getenv("AYUSHBOT_FL_SERVER", fl_cfg.get("server_address", "127.0.0.1:8080"))
    model_path = os.getenv("AYUSHBOT_XGB_MODEL_PATH", fl_cfg.get("model_path", "/opt/ayushbot/models/triage_xgb.json"))
    train_data_path = os.getenv("AYUSHBOT_FL_TRAIN_DATA", fl_cfg.get("train_data_path", "/opt/ayushbot/data/fl_train.npz"))
    eval_data_path = os.getenv("AYUSHBOT_FL_EVAL_DATA", fl_cfg.get("eval_data_path", "/opt/ayushbot/data/fl_eval.npz"))
    return FLConfig(
        server_address=server_address,
        model_path=model_path,
        train_data_path=train_data_path,
        eval_data_path=eval_data_path,
        local_epochs=int(fl_cfg.get("local_epochs", 3)),
        learning_rate=float(fl_cfg.get("learning_rate", 0.01)),
        min_batch_size=int(fl_cfg.get("min_batch_size", 10)),
        dp_epsilon=float(fl_cfg.get("dp_epsilon", 1.0)),
        dp_delta=float(fl_cfg.get("dp_delta", 1e-6)),
        dp_max_grad_norm=float(fl_cfg.get("dp_max_grad_norm", 1.0)),
    )


def _load_dataset(path: str) -> Tuple[np.ndarray, np.ndarray]:
    if not os.path.exists(path):
        return np.empty((0, 0), dtype=np.float32), np.empty((0,), dtype=np.int64)
    data = np.load(path)
    return data["X"].astype(np.float32), data["y"].astype(np.int64)


def _booster_from_bytes(raw: bytes) -> xgb.Booster:
    booster = xgb.Booster()
    booster.load_model(raw)
    return booster


def _booster_to_ndarrays(booster: xgb.Booster) -> List[np.ndarray]:
    raw = booster.save_raw()
    return [np.frombuffer(raw, dtype=np.uint8)]


def _ndarrays_to_booster(ndarrays: List[np.ndarray]) -> xgb.Booster:
    raw = ndarrays[0].tobytes()
    return _booster_from_bytes(raw)


def _train_local(booster: xgb.Booster, X: np.ndarray, y: np.ndarray, cfg: FLConfig) -> xgb.Booster:
    dtrain = xgb.DMatrix(X, label=y)
    params = {
        "learning_rate": cfg.learning_rate,
        "objective": "multi:softprob",
        "num_class": 4,
        "eval_metric": "mlogloss",
    }
    return xgb.train(params, dtrain, num_boost_round=cfg.local_epochs, xgb_model=booster)


class XGBoostFlowerClient(fl.client.NumPyClient):
    def __init__(self, cfg: FLConfig) -> None:
        self.cfg = cfg
        self._booster: xgb.Booster | None = None

    def _load_model(self, parameters: List[np.ndarray] | None = None) -> xgb.Booster:
        if parameters is not None:
            self._booster = _ndarrays_to_booster(parameters)
            return self._booster
        if self._booster is None:
            if os.path.exists(self.cfg.model_path):
                self._booster = xgb.Booster()
                self._booster.load_model(self.cfg.model_path)
            else:
                self._booster = xgb.Booster()
        return self._booster

    def get_parameters(self, config: Dict[str, Any] | None = None) -> List[np.ndarray]:
        booster = self._load_model()
        return _booster_to_ndarrays(booster)

    def fit(
        self,
        parameters: List[np.ndarray],
        config: Dict[str, Any] | None = None,
    ) -> Tuple[List[np.ndarray], int, Dict[str, Any]]:
        booster = self._load_model(parameters)
        old_raw = _booster_to_ndarrays(booster)[0].astype(np.float32)
        X, y = _load_dataset(self.cfg.train_data_path)
        if X.size == 0 or y.size == 0 or len(y) < self.cfg.min_batch_size:
            return _booster_to_ndarrays(booster), 0, {"status": "no-data"}

        updated = _train_local(booster, X, y, self.cfg)
        if self.cfg.model_path:
            updated.save_model(self.cfg.model_path)

        new_raw = _booster_to_ndarrays(updated)[0].astype(np.float32)
        gradient = new_raw - old_raw
        dp_update, stats = apply_dp(
            gradient,
            max_norm=self.cfg.dp_max_grad_norm,
            epsilon=self.cfg.dp_epsilon,
            delta=self.cfg.dp_delta,
        )
        dp_raw = np.clip(old_raw + dp_update, 0, 255).astype(np.uint8)
        metrics = {"dp": stats, "status": "dp-clipped"}

        return [dp_raw], len(y), metrics

    def evaluate(
        self, parameters: List[np.ndarray], config: Dict[str, Any] | None = None
    ) -> Tuple[float, int, Dict[str, Any]]:
        booster = self._load_model(parameters)
        X, y = _load_dataset(self.cfg.eval_data_path)
        if X.size == 0 or y.size == 0:
            return 0.0, 0, {"status": "no-data"}
        dtest = xgb.DMatrix(X, label=y)
        preds = booster.predict(dtest)
        labels = np.argmax(preds, axis=1)
        accuracy = float((labels == y).mean())
        return 1.0 - accuracy, len(y), {"accuracy": accuracy}


def start_client() -> None:
    cfg = _build_config()
    client = XGBoostFlowerClient(cfg)
    fl.client.start_numpy_client(server_address=cfg.server_address, client=client)


def create_client() -> XGBoostFlowerClient:
    return XGBoostFlowerClient(_build_config())