# =============================================================================
# AyushBot Backend — API Middleware: Rate Limiter
# =============================================================================
#
# PURPOSE:
#   Limits the rate of incoming HTTP requests to prevent accidental overload
#   of the Raspberry Pi 4 gateway. Since the gateway has limited CPU and
#   memory, uncontrolled request bursts (from buggy app versions or multiple
#   ASHAs connecting simultaneously) could degrade triage performance.
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
