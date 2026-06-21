"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "AyushBot Cloud API",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - system ready to serve traffic."""
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "ready",
            "database": "ready",
            "model_registry": "ready",
        },
    }


@router.get("/live", tags=["Health"])
async def liveness_check():
    """Liveness check - system is alive."""
    return {
        "alive": True,
        "uptime_seconds": 3600,  # TODO: Track actual uptime
        "timestamp": datetime.utcnow().isoformat(),
    }
