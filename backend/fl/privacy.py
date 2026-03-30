"""AyushBot Backend — DP clipping utilities for FL updates."""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np


def l2_norm(vector: np.ndarray) -> float:
    return float(np.linalg.norm(vector))


def clip_by_l2(vector: np.ndarray, max_norm: float) -> Tuple[np.ndarray, float]:
    norm = l2_norm(vector)
    if norm == 0.0:
        return vector, norm
    scale = min(1.0, max_norm / norm)
    return vector * scale, norm


def gaussian_noise(stddev: float, shape: tuple[int, ...]) -> np.ndarray:
    return np.random.normal(0.0, stddev, size=shape).astype(np.float32)


def calibrate_noise(
    epsilon: float, delta: float, max_norm: float
) -> float:
    if epsilon <= 0:
        raise ValueError("epsilon must be > 0")
    if delta <= 0 or delta >= 1:
        raise ValueError("delta must be in (0,1)")
    return max_norm * math.sqrt(2 * math.log(1.25 / delta)) / epsilon


def apply_dp(
    gradient: np.ndarray,
    max_norm: float,
    epsilon: float,
    delta: float,
    add_noise: bool = True,
) -> Tuple[np.ndarray, dict]:
    clipped, norm = clip_by_l2(gradient, max_norm)
    sigma = calibrate_noise(epsilon, delta, max_norm)
    if add_noise:
        clipped = clipped + gaussian_noise(sigma, clipped.shape)
    return clipped, {
        "grad_norm": norm,
        "max_norm": max_norm,
        "epsilon": epsilon,
        "delta": delta,
        "sigma": sigma,
    }
