"""
Security helpers.

* `require_admin` protects destructive or expensive endpoints. If ADMIN_TOKEN is configured, the
  request must carry `X-Admin-Token` with that exact value (compared in constant time).
* `SecurityHeadersMiddleware` adds standard defensive HTTP headers to every response.
"""
import hmac
from typing import Optional

from fastapi import Header, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


def require_admin(x_admin_token: Optional[str] = Header(default=None)) -> None:
    expected = settings.ADMIN_TOKEN
    if not expected:
        return  # local development: no token configured
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), expected.encode()):
        raise HTTPException(
            status_code=401,
            detail="This action needs the admin token (Demo controls → Admin token).",
        )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def cors_settings() -> dict:
    origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()] or ["*"]
    wildcard = origins == ["*"]
    return {
        "allow_origins": origins,
        # Credentials are never combined with a wildcard origin (that would let any site act as the user).
        "allow_credentials": not wildcard,
        "allow_methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-Admin-Token"],
    }
