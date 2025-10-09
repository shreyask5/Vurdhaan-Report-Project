"""
Rate Limiting Middleware for Flask API
Provides IP-based and user-based rate limiting
"""

from flask import request, g, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from typing import Optional, Callable
import time


class RateLimiter:
    """
    Advanced rate limiter with per-IP and per-user limits
    """

    def __init__(self, app=None):
        self.limiter = None
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize rate limiter with Flask app"""
        # Respect config toggle: allow disabling for testing
        enabled = app.config.get('RATELIMIT_ENABLED', True)
        if not enabled:
            self.limiter = None
            print("⚠️ Rate limiter disabled via RATELIMIT_ENABLED=False")
            return

        # Storage and defaults from config
        storage_uri = app.config.get('RATELIMIT_STORAGE_URI', 'memory://')
        default_limits = app.config.get('RATELIMIT_DEFAULT_LIMITS', ["120 per minute"])

        # Initialize Flask-Limiter
        self.limiter = Limiter(
            key_func=get_remote_address,
            app=app,
            storage_uri=storage_uri,
            default_limits=default_limits,
            headers_enabled=True,  # Add X-RateLimit-* headers
            swallow_errors=True  # Don't crash on Redis errors
        )

        print(f"✅ Rate limiter initialized with storage: {storage_uri} limits: {default_limits}")

    def get_user_id(self) -> Optional[str]:
        """Get user ID from Flask g object if authenticated"""
        if hasattr(g, 'user') and g.user:
            return g.user.get('uid')
        return None

    def user_or_ip(self) -> str:
        """Get unique identifier: user ID if authenticated, else IP"""
        user_id = self.get_user_id()
        if user_id:
            return f"user:{user_id}"
        return f"ip:{get_remote_address()}"


# Global rate limiter instance
rate_limiter = RateLimiter()


def limit_by_user(limit_string: str):
    """
    Rate limit by authenticated user ID (or IP if not authenticated)

    Usage:
        @app.post('/api/projects')
        @require_auth
        @limit_by_user("10 per hour")
        def create_project():
            pass

    Args:
        limit_string: Rate limit in format "X per Y" (e.g., "10 per hour", "60 per minute")
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not rate_limiter.limiter:
                # Rate limiter not initialized, skip
                return f(*args, **kwargs)

            # Get unique identifier (user or IP)
            key = rate_limiter.user_or_ip()

            # Apply limit using Flask-Limiter's decorator
            limited_func = rate_limiter.limiter.limit(
                limit_string,
                key_func=lambda: key,
                error_message="Rate limit exceeded. Please try again later."
            )(f)

            return limited_func(*args, **kwargs)

        return wrapper
    return decorator


def limit_by_ip(limit_string: str):
    """
    Rate limit by IP address only

    Usage:
        @app.post('/api/public/upload')
        @limit_by_ip("5 per hour")
        def public_upload():
            pass
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not rate_limiter.limiter:
                return f(*args, **kwargs)

            limited_func = rate_limiter.limiter.limit(
                limit_string,
                key_func=get_remote_address
            )(f)

            return limited_func(*args, **kwargs)

        return wrapper
    return decorator


def limit_expensive(limit_string: str = "10 per hour"):
    """
    Stricter rate limit for expensive operations (uploads, reports, etc.)

    Usage:
        @app.post('/api/projects/<id>/report')
        @require_auth
        @limit_expensive("5 per hour")
        def generate_report(id):
            pass
    """
    return limit_by_user(limit_string)


class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded"""
    pass


def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """
    Manual rate limit check (for custom logic)

    Args:
        key: Unique key for the resource
        limit: Maximum number of requests
        window: Time window in seconds

    Returns:
        True if within limit, False if exceeded
    """
    # Simple in-memory rate limiting (use Redis in production)
    if not hasattr(g, '_rate_limit_storage'):
        g._rate_limit_storage = {}

    current_time = time.time()
    storage = g._rate_limit_storage

    if key not in storage:
        storage[key] = []

    # Remove expired timestamps
    storage[key] = [ts for ts in storage[key] if current_time - ts < window]

    # Check if limit exceeded
    if len(storage[key]) >= limit:
        return False

    # Add current timestamp
    storage[key].append(current_time)
    return True


def get_rate_limit_headers(limit: int, remaining: int, reset_time: int) -> dict:
    """
    Generate X-RateLimit-* headers

    Args:
        limit: Total limit
        remaining: Remaining requests
        reset_time: Unix timestamp when limit resets

    Returns:
        Dict of headers
    """
    return {
        'X-RateLimit-Limit': str(limit),
        'X-RateLimit-Remaining': str(remaining),
        'X-RateLimit-Reset': str(reset_time)
    }


def exempt_from_rate_limit(f):
    """
    Decorator to exempt a route from rate limiting

    Usage:
        @app.get('/api/health')
        @exempt_from_rate_limit
        def health_check():
            return {'status': 'ok'}
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if rate_limiter.limiter:
            # Mark as exempt
            rate_limiter.limiter.exempt(f)
        return f(*args, **kwargs)
    return wrapper
