# =============================================================================
# AyushBot Backend — API Middleware: Rate Limiter
# =============================================================================
#
# PURPOSE:
#   Limits the rate of incoming HTTP requests to prevent accidental overload
#   of the local PHC gateway host. Uncontrolled request bursts from buggy app
#   versions or multiple ASHAs connecting simultaneously could degrade triage
#   and sync performance.
#
# IMPLEMENTATION APPROACH:
#   Token bucket algorithm (or sliding window counter):
#     - Each authenticated client (identified by API key or ASHA ID) gets
#       a token bucket with:
#       - max_tokens: 10 (burst capacity)
#       - refill_rate: 2 tokens per second (sustained throughput)
#     - Each request consumes 1 token
#     - If bucket is empty, return HTTP 429 Too Many Requests with:
#       - Retry-After header indicating seconds until next available token
#       - JSON body with error message
#
# EXEMPT ROUTES:
#   Some endpoints are excluded from rate limiting:
#     - /api/v1/health/ping — Must always respond for connectivity checks
#     - /api/v1/health/metrics — Prometheus scraping should not be throttled
#
# TRIAGE PRIORITY:
#   The rate limiter is lenient by design — the gateway typically serves
#   only 1-5 concurrent ASHAs. The limiter exists as a safety valve, not
#   as a primary access control mechanism.
#
# STORAGE:
#   Token counts are stored in-memory (dict keyed by client ID). No
#   persistence needed — rate limits reset on gateway restart.
#
# CONFIGURATION (config.yaml):
#   - rate_limit_max_tokens: int (default: 10)
#   - rate_limit_refill_rate: float (default: 2.0 tokens/sec)
#   - rate_limit_exempt_paths: list[str]
# =============================================================================

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass
class Bucket:
	tokens: float
	last_refill: float


class RateLimiterMiddleware(BaseHTTPMiddleware):
	def __init__(
		self,
		app,
		max_tokens: int = 10,
		refill_rate: float = 2.0,
		exempt_paths: List[str] | None = None,
	) -> None:
		super().__init__(app)
		self.max_tokens = max_tokens
		self.refill_rate = refill_rate
		self.exempt_paths = exempt_paths or ["/api/v1/health/ping", "/api/v1/health/metrics"]
		self._buckets: Dict[str, Bucket] = {}

	def _key(self, request: Request) -> str:
		auth = request.headers.get("authorization")
		if auth:
			return auth[-16:]
		return request.client.host if request.client else "unknown"

	def _refill(self, bucket: Bucket) -> None:
		now = time.time()
		elapsed = now - bucket.last_refill
		bucket.tokens = min(self.max_tokens, bucket.tokens + elapsed * self.refill_rate)
		bucket.last_refill = now

	async def dispatch(self, request: Request, call_next):
		if request.url.path in self.exempt_paths:
			return await call_next(request)

		key = self._key(request)
		bucket = self._buckets.get(key)
		if not bucket:
			bucket = Bucket(tokens=float(self.max_tokens), last_refill=time.time())
			self._buckets[key] = bucket

		self._refill(bucket)
		if bucket.tokens < 1.0:
			retry_after = max(1, int((1.0 - bucket.tokens) / self.refill_rate))
			return JSONResponse(
				status_code=429,
				content={"detail": "Rate limit exceeded"},
				headers={"Retry-After": str(retry_after)},
			)

		bucket.tokens -= 1.0
		return await call_next(request)
