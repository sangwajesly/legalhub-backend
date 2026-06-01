"""
Custom High-Performance In-Memory Token Bucket Rate Limiter for FastAPI.
Zero external dependencies, ultra-lightweight, and fully asynchronous.
"""

import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException, status

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """
    Thread-safe and fast in-memory sliding token bucket rate limiter.
    Identifies clients by their IP Address or User ID if authenticated.
    """
    
    def __init__(self, requests_per_minute: float, capacity: int, name: str = "API"):
        """
        Args:
            requests_per_minute: Number of allowed requests per minute.
            capacity: Maximum burst capacity of the bucket.
            name: Human-readable name of the limiter (e.g., 'Chat', 'Session') for logs.
        """
        self.rate = requests_per_minute / 60.0  # Convert to tokens per second
        self.capacity = capacity
        self.name = name
        # Track buckets per client: {client_key: (current_tokens, last_update_timestamp)}
        self.buckets = defaultdict(lambda: (float(capacity), time.time()))

    async def __call__(self, request: Request):
        """
        FastAPI dependency callable.
        Examines the request to determine client identity and verify limits.
        """
        # Determine unique client key (fallback to client IP address if user not identified)
        client_key = request.client.host if request.client else "unknown-ip"
        
        # Check if auth header or state has user info to be more precise
        if hasattr(request.state, "user") and request.state.user:
            client_key = getattr(request.state.user, "uid", client_key)
        elif "authorization" in request.headers:
            # Quick string hash of authorization header for identity if JWT parsed upstream
            auth_header = request.headers["authorization"]
            client_key = f"auth:{hash(auth_header)}"

        now = time.time()
        tokens, last_update = self.buckets[client_key]

        # Calculate leaked/refilled tokens based on elapsed time
        elapsed = now - last_update
        tokens = min(float(self.capacity), tokens + (elapsed * self.rate))

        # Check if client has at least 1 token
        if tokens < 1.0:
            # Bucket is exhausted. Calculate wait time for the next token to refill
            wait_time = int((1.0 - tokens) / self.rate) + 1
            logger.warning(
                f"Rate limit exceeded on '{self.name}' endpoint by client {client_key}. "
                f"Wait time: {wait_time}s."
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RateLimitExceeded",
                    "message": f"You are sending requests too fast! Please wait {wait_time} seconds.",
                    "retry_after": wait_time
                },
                headers={"Retry-After": str(wait_time)}
            )

        # Consume 1 token and save state
        self.buckets[client_key] = (tokens - 1.0, now)
        logger.debug(
            f"Limiter '{self.name}': Client {client_key} consumed 1 token. "
            f"Remaining: {tokens - 1.0:.2f}/{self.capacity}"
        )
