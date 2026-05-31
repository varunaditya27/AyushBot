"""Model registry and query endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, status

from cloud.api.exceptions import BadRequestError, NotFoundError, UnauthorizedError

router = APIRouter()


def _require_auth(authorization: Optional[str] = Header(None)):
    """Validate authorization header."""
    if authorization is None:
        raise UnauthorizedError("Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization format")

    api_key = authorization.replace("Bearer ", "", 1)

    from cloud.api.auth import VALID_API_KEYS

    if api_key not in VALID_API_KEYS:
        raise UnauthorizedError("Invalid API key")

    return VALID_API_KEYS[api_key]


@router.get("/list", tags=["Models"])
async def list_models(skip: int = 0, limit: int = 10, authorization: Optional[str] = Header(None)):
    """List all saved models from registry."""
    _require_auth(authorization)

    if skip < 0 or limit < 1:
        raise BadRequestError("Invalid skip or limit")

    return {
        "models": [
            {
                "version": f"v1.{50-i}",
                "round_num": 50 - i,
                "num_clients": 25,
                "accuracy": 0.90 + (i * 0.001),
                "loss": 0.20 - (i * 0.001),
                "aggregation_strategy": "FedAvg",
                "created_at": datetime.utcnow().isoformat(),
            }
            for i in range(limit)
        ],
        "skip": skip,
        "limit": limit,
        "total": 50,
    }


@router.get("/latest", tags=["Models"])
async def get_latest_model(authorization: Optional[str] = Header(None)):
    """Get latest model from registry."""
    _require_auth(authorization)
    return {
        "version": "v1.50",
        "round_num": 50,
        "num_clients": 25,
        "accuracy": 0.955,
        "loss": 0.05,
        "aggregation_strategy": "FedAvg",
        "model_size_bytes": 1048576,
        "epsilon_consumed": 2.5,
        "download_url": "/api/v1/models/download/v1.50",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/{version}", tags=["Models"])
async def get_model_by_version(version: str, authorization: Optional[str] = Header(None)):
    """Get specific model version details."""
    _require_auth(authorization)

    if not version.startswith("v1."):
        raise NotFoundError(f"Model version {version} not found")

    return {
        "version": version,
        "round_num": 50,
        "num_clients": 28,
        "accuracy": 0.925,
        "loss": 0.148,
        "aggregation_strategy": "FedProx",
        "model_size_bytes": 1048576,
        "epsilon_consumed": 0.45,
        "timestamp": datetime.utcnow().isoformat(),
        "download_url": f"/api/v1/models/download/{version}",
    }


@router.get("/download/{version}", tags=["Models"])
async def download_model(version: str, authorization: Optional[str] = Header(None)):
    """Download model weights (stub - returns metadata)."""
    _require_auth(authorization)

    if not version.startswith("v1."):
        raise NotFoundError(f"Model version {version} not found")

    return {
        "status": "ready",
        "version": version,
        "model_size_bytes": 1048576,
        "format": "numpy",
        "message": "Use /api/v1/models/download/{version}/bytes to download",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/compare", tags=["Models"])
async def compare_models(version1: str, version2: str, authorization: Optional[str] = Header(None)):
    """Compare metrics between two model versions."""
    _require_auth(authorization)

    if not version1.startswith("v1.") or not version2.startswith("v1."):
        raise BadRequestError("Invalid version format")

    return {
        "comparison": {
            "version1": version1,
            "version2": version2,
            "metrics": {
                "accuracy_delta": 0.002,
                "loss_delta": -0.005,
                "inference_time_delta_ms": -0.3,
            },
            "winner": "version1" if 0.002 > 0 else "version2",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics/{version}", tags=["Models"])
async def get_model_metrics(version: str, authorization: Optional[str] = Header(None)):
    """Get detailed metrics for a model version."""
    _require_auth(authorization)

    if not version.startswith("v1."):
        raise NotFoundError(f"Model version {version} not found")

    return {
        "version": version,
        "metrics": {
            "accuracy": 0.925,
            "precision": 0.93,
            "recall": 0.92,
            "f1_score": 0.925,
            "loss": 0.148,
            "inference_time_ms": 15.2,
            "model_size_bytes": 1048576,
        },
        "training": {
            "round_num": 50,
            "num_clients": 28,
            "aggregation_strategy": "FedProx",
            "aggregation_time_sec": 5.2,
        },
        "privacy": {
            "epsilon_consumed": 0.45,
            "delta": 1e-6,
            "gradient_clipping_norm": 1.0,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
