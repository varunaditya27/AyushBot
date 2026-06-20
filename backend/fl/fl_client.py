"""AyushBot Backend — Flower FL client for XGBoost triage model."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import numpy as np

from backend.config import get_settings

if TYPE_CHECKING:
	import xgboost as xgb

logger = logging.getLogger(__name__)

try:
	import flwr as fl
except ImportError:
	fl = None  # type: ignore[assignment]


@dataclass
class FLConfig:
    enabled: bool
    training_enabled: bool
    update_representation: str
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


def _build_config() -> FLConfig:
    fl_cfg = get_settings().fl
    return FLConfig(
        enabled=fl_cfg.enabled,
        training_enabled=fl_cfg.training_enabled,
        update_representation=fl_cfg.update_representation,
        server_address=fl_cfg.server_address,
        model_path=str(fl_cfg.model_path),
        train_data_path=str(fl_cfg.train_data_path),
        eval_data_path=str(fl_cfg.eval_data_path),
        local_epochs=fl_cfg.local_epochs,
        learning_rate=fl_cfg.learning_rate,
        min_batch_size=fl_cfg.min_batch_size,
        dp_epsilon=fl_cfg.dp_epsilon,
        dp_delta=fl_cfg.dp_delta,
        dp_max_grad_norm=fl_cfg.dp_max_grad_norm,
    )


def _load_dataset(path: str) -> Tuple[np.ndarray, np.ndarray]:
    if not Path(path).exists():
        return np.empty((0, 0), dtype=np.float32), np.empty((0,), dtype=np.int64)
    data = np.load(path)
    return data["X"].astype(np.float32), data["y"].astype(np.int64)


def _xgboost():
    try:
        import xgboost as xgb
    except ImportError as exc:
        raise RuntimeError("xgboost is required for federated training") from exc
    return xgb


def _booster_from_bytes(raw: bytes) -> "xgb.Booster":
    xgb = _xgboost()
    booster = xgb.Booster()
    booster.load_model(raw)
    return booster


def _booster_to_ndarrays(booster: "xgb.Booster") -> List[np.ndarray]:
    raw = booster.save_raw()
    return [np.frombuffer(raw, dtype=np.uint8)]


def _ndarrays_to_booster(ndarrays: List[np.ndarray]) -> "xgb.Booster":
    raw = ndarrays[0].tobytes()
    return _booster_from_bytes(raw)


def _train_local(
    booster: "xgb.Booster", X: np.ndarray, y: np.ndarray, cfg: FLConfig
) -> "xgb.Booster":
    raise NotImplementedError(
        "Federated XGBoost training is disabled: this backend does not yet "
        "implement a safe structured model-update representation. DP noise "
        "must not be applied to serialized model bytes."
    )


_NumPyClientBase = fl.client.NumPyClient if fl is not None else object


class XGBoostFlowerClient(_NumPyClientBase):
    def __init__(self, cfg: FLConfig) -> None:
        self.cfg = cfg
        self._booster: "xgb.Booster | None" = None

    def _load_model(self, parameters: List[np.ndarray] | None = None) -> "xgb.Booster":
        xgb = _xgboost()
        if parameters is not None:
            self._booster = _ndarrays_to_booster(parameters)
            return self._booster
        if self._booster is None:
            if Path(self.cfg.model_path).exists():
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
        if not self.cfg.training_enabled:
            raise RuntimeError(
                "Federated training is disabled by configuration "
                "(fl.training_enabled=false)."
            )
        if self.cfg.update_representation == "not_implemented":
            raise NotImplementedError(
                "Federated training requires a structured update representation; "
                "serialized model-byte DP updates are intentionally disabled."
            )
        booster = self._load_model(parameters)
        X, y = _load_dataset(self.cfg.train_data_path)
        if X.size == 0 or y.size == 0 or len(y) < self.cfg.min_batch_size:
            return _booster_to_ndarrays(booster), 0, {"status": "no-data"}

        updated = _train_local(booster, X, y, self.cfg)
        if self.cfg.model_path:
            updated.save_model(self.cfg.model_path)

        return _booster_to_ndarrays(updated), len(y), {"status": "trained"}

    def evaluate(
        self, parameters: List[np.ndarray], config: Dict[str, Any] | None = None
    ) -> Tuple[float, int, Dict[str, Any]]:
        booster = self._load_model(parameters)
        X, y = _load_dataset(self.cfg.eval_data_path)
        if X.size == 0 or y.size == 0:
            return 0.0, 0, {"status": "no-data"}
        xgb = _xgboost()
        dtest = xgb.DMatrix(X, label=y)
        preds = booster.predict(dtest)
        labels = np.argmax(preds, axis=1)
        accuracy = float((labels == y).mean())
        return 1.0 - accuracy, len(y), {"accuracy": accuracy}


def start_client() -> None:
    cfg = _build_config()
    if not cfg.enabled:
        raise RuntimeError("Federated learning client is disabled (fl.enabled=false)")
    if cfg.training_enabled or cfg.update_representation != "not_implemented":
        raise NotImplementedError(
            "Federated training is incomplete and cannot be started safely."
        )
    if fl is None:
        raise RuntimeError("flwr is required to start the federated learning client")
    client = XGBoostFlowerClient(cfg)
    fl.client.start_numpy_client(server_address=cfg.server_address, client=client)


def create_client() -> XGBoostFlowerClient:
    return XGBoostFlowerClient(_build_config())
