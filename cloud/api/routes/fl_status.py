"""FL server status and management endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, status

from cloud.api.exceptions import BadRequestError, NotFoundError, UnauthorizedError

router = APIRouter()


def _require_auth(authorization: Optional[str] = Header(None)):
    """Validate authorization header."""
    if authorization is None:
        raise UnauthorizedError("Missing authorization header")

    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization format. Use 'Bearer <api_key>'")

    api_key = authorization.replace("Bearer ", "", 1)

    from cloud.api.auth import VALID_API_KEYS

    if api_key not in VALID_API_KEYS:
        raise UnauthorizedError("Invalid API key")

    return VALID_API_KEYS[api_key]


@router.get("/status", tags=["FL Server"])
async def get_fl_status(user=Header(None, alias="Authorization")):
    """Get current FL server status."""
    _require_auth(user)

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
async def list_fl_rounds(skip: int = 0, limit: int = 10, authorization: Optional[str] = Header(None)):
    """List FL round history."""
    _require_auth(authorization)

    if skip < 0 or limit < 1:
        raise BadRequestError("Invalid skip or limit parameters")

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
async def get_fl_round(round_num: int, authorization: Optional[str] = Header(None)):
    """Get details of a specific FL round."""
    _require_auth(authorization)

    if round_num < 1 or round_num > 50:
        raise NotFoundError(f"Round {round_num} not found")

    return {
        "round_num": round_num,
        "status": "completed",
        "num_clients": 25,
        "client_list": [f"GW{i:03d}" for i in range(25)],
        "aggregation_time_sec": 5.2,
        "accuracy": 0.92,
        "loss": 0.15,
        "epsilon_consumed": 0.05,
        "model_size_bytes": 1048576,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/rounds/trigger", tags=["FL Server"])
async def trigger_fl_round(authorization: Optional[str] = Header(None)):
    """Manually trigger an FL round."""
    user = _require_auth(authorization)

    # Verify admin role
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can trigger rounds",
        )

    return {
        "status": "triggered",
        "round_num": 51,
        "message": "FL round 51 triggered successfully",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/config", tags=["FL Server"])
async def get_fl_config(authorization: Optional[str] = Header(None)):
    """Get FL server configuration."""
    _require_auth(authorization)

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

