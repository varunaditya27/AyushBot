"""FL server status and management endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/status", tags=["FL Server"])
async def get_fl_status():
    """Get current FL server status."""
    return {
        "server_running": True,
        "current_round": 42,
        "total_rounds": 50,
        "min_fit_clients": 10,
        "available_clients": 28,
        "aggregation_strategy": "FedAvg",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/rounds", tags=["FL Server"])
async def list_fl_rounds(skip: int = 0, limit: int = 10):
    """List FL round history."""
    if skip < 0 or limit < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid skip or limit",
        )

    return {
        "rounds": [
            {
                "round_num": 50 - i,
                "status": "completed",
                "num_clients": 25 + (i % 5),
                "aggregation_time_sec": 5.2 + (i * 0.1),
                "accuracy": 0.92 + (i * 0.001),
                "timestamp": datetime.utcnow().isoformat(),
            }
            for i in range(limit)
        ],
        "skip": skip,
        "limit": limit,
        "total": 50,
    }


@router.get("/rounds/{round_num}", tags=["FL Server"])
async def get_fl_round(round_num: int):
    """Get details of a specific FL round."""
    if round_num < 1 or round_num > 50:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Round {round_num} not found",
        )

    return {
        "round_num": round_num,
        "status": "completed",
        "num_clients": 25,
        "client_list": [
            f"GW{i:03d}" for i in range(25)
        ],
        "aggregation_time_sec": 5.2,
        "accuracy": 0.92,
        "loss": 0.15,
        "epsilon_consumed": 0.05,
        "model_size_bytes": 1048576,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/rounds/trigger", tags=["FL Server"])
async def trigger_fl_round():
    """Manually trigger an FL round."""
    return {
        "status": "triggered",
        "round_num": 51,
        "message": "FL round 51 triggered successfully",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/config", tags=["FL Server"])
async def get_fl_config():
    """Get FL server configuration."""
    return {
        "port": 8080,
        "strategy": "FedAvg",
        "min_fit_clients": 10,
        "min_available_clients": 10,
        "min_fit_accuracy": 0.85,
        "rounds": 50,
        "epochs": 1,
        "batch_size": 32,
        "learning_rate": 0.01,
        "privacy": {
            "enabled": True,
            "epsilon": 1.0,
            "delta": 1e-6,
            "gradient_clipping_norm": 1.0,
        },
        "timeout_seconds": 600,
    }
