import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


STRICT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}

# (requests, window_seconds)
DEFAULT_LIMIT = (120, 60)   # 120 req / 60 s  per IP
STRICT_LIMIT  = (10,  60)   # 10  req / 60 s  per IP


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    sliding window rate limiter — I have used a traffic control algorithm to prevent abuse of API.
    """

    def __init__(self, app):
        super().__init__(app)
        
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_allowed(self, ip: str, path: str) -> bool:
        max_reqs, window = STRICT_LIMIT if path in STRICT_PATHS else DEFAULT_LIMIT
        now = time.monotonic()
        cutoff = now - window
        timestamps = self._buckets[ip]

        # Drop timestamps outside the window
        self._buckets[ip] = [t for t in timestamps if t > cutoff]

        if len(self._buckets[ip]) >= max_reqs:
            return False

        self._buckets[ip].append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        ip = self._client_ip(request)
        if not self._is_allowed(ip, request.url.path):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down and try again."},
                headers={"Retry-After": "60"},
            )
        return await call_next(request)