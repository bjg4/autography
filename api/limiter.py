"""Shared rate limiter for all API endpoints."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Single rate limiter instance used across all routers
limiter = Limiter(key_func=get_remote_address)
