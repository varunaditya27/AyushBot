"""Model registry and query endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/list", tags=["Models"])
async def list_models(skip: int = 0, limit: int = 10):
    """List all saved models from registry."""
    if skip < 0 or limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid skip or limit",
        )

    return {
        "models": [
            {
                "version": f"v_1_2026_05_31_{(50 - i):02d}0000_000000",
                "round_num": 50 - i,
                "num_clients": 25 + (i % 5),
                "accuracy": 0.92 + (i * 0.001),
                "loss": 0.15 - (i * 0.0005),
                "aggregation_strategy": "FedAvg" if (50 - i) < 26 else "FedProx",
                "model_size_bytes": 1048576,
                "timestamp": datetime.utcnow().isoformat(),
            }
            for i in range(limit)
        ],
        "skip": skip,
        "limit": limit,
        "total": 50,
    }


@router.get("/latest", tags=["Models"])
async def get_latest_model():
    """Get latest model from registry."""
    return {
        "version": "v_1_2026_05_31_5000_000000",
        "round_num": 50,
        "num_clients": 28,
        "accuracy": 0.925,
        "loss": 0.148,
        "aggregation_strategy": "FedProx",
        "model_size_bytes": 1048576,
        "epsilon_consumed": 0.45,
        "timestamp": datetime.utcnow().isoformat(),
        "download_url": "/api/v1/models/download/v_1_2026_05_31_5000_000000",
    }


@router.get("/{version}", tags=["Models"])
async def get_model_by_version(version: str):
    """Get specific model version details."""
    if not version.startswith("v_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {version} not found",
        )

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
async def download_model(version: str):
    """Download model weights (stub - returns metadata)."""
    if not version.startswith("v_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {version} not found",
        )

    return {
        "status": "ready",
        "version": version,
        "model_size_bytes": 1048576,
        "format": "numpy",
        "message": "Use /api/v1/models/download/{version}/bytes to download",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/compare", tags=["Models"])
async def compare_models(version1: str, version2: str):
    """Compare metrics between two model versions."""
    if not version1.startswith("v_") or not version2.startswith("v_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid version format",
        )

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
async def get_model_metrics(version: str):
    """Get detailed metrics for a model version."""
    if not version.startswith("v_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model version {version} not found",
        )

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
