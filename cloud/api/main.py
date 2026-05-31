"""FastAPI REST API for AyushBot Cloud - FL Server Integration."""

import sys
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cloud.api.exceptions import APIException
from cloud.api.middleware.rate_limit import RateLimitMiddleware
from cloud.api.routes import health, fl_status, model

# Initialize FastAPI app
app = FastAPI(
    title="AyushBot Cloud API",
    description="REST API for Federated Learning & Analytics",
    version="1.0.0",
)

# Configure CORS
origins = [
    "http://localhost:3000",  # Mobile app dev
    "http://localhost:8501",  # Streamlit dashboard
    "http://localhost:8080",  # FL server gRPC bridge (if needed)
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8501",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limiting middleware (60 req/min per IP)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """API root - basic health check."""
    return {
        "status": "ok",
        "service": "AyushBot Cloud API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Include routers
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(fl_status.router, prefix="/api/v1/fl", tags=["FL Server"])
app.include_router(model.router, prefix="/api/v1/models", tags=["Models"])


# Error handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": "HTTP_ERROR",
            "status_code": exc.status_code,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unhandled errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "status_code": 500,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("🚀 AyushBot Cloud API starting...")
    print("📊 Endpoints available at /docs (Swagger) or /redoc (ReDoc)")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("🛑 AyushBot Cloud API shutting down...")


if __name__ == "__main__":
    # Development server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8443,
        ssl_keyfile=None,  # TLS to be added in Phase 5
        ssl_certfile=None,
    )
