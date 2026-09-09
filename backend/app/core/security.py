"""
AegisAI Security Compatibility Shim.

Forwards all security and auth utilities to canonical `app.core.security.jwt`.
"""

from app.core.security.jwt import (
    RequireRole,
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
    get_current_active_user,
    get_current_user,
    get_optional_user,
    hash_password,
    oauth2_scheme,
    verify_password,
)

__all__ = [
    "RequireRole",
    "create_access_token",
    "create_refresh_token",
    "create_token",
    "decode_token",
    "get_current_active_user",
    "get_current_user",
    "get_optional_user",
    "hash_password",
    "oauth2_scheme",
    "verify_password",
]
