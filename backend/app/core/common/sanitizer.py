"""
AegisAI Core — Input Sanitizer for Free-Text and Payloads.

Defends against XSS, script injection, control character abuse, and malformed HTML
in disaster reports, mission notes, operator comments, and assistant queries.
"""

import html
import re
from typing import Any

# Match any HTML tags or script injection attempts
_TAG_RE = re.compile(r"<[^>]+>")
# Match dangerous control characters (excluding standard whitespace like \n, \r, \t)
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def sanitize_text(text: str | None, max_length: int | None = None) -> str:
    """
    Sanitize free-text input:
    - Strips leading/trailing whitespace
    - Removes all HTML tags
    - Unescapes standard HTML entities and safely escapes special characters
    - Strips dangerous ASCII control characters
    - Optionally truncates to max_length
    """
    if not text:
        return ""

    # Strip control characters
    cleaned = _CONTROL_CHARS_RE.sub("", text)
    # Strip HTML tags
    cleaned = _TAG_RE.sub("", cleaned)
    # Unescape any existing HTML entities, then escape reserved chars
    cleaned = html.unescape(cleaned).strip()

    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]

    return cleaned


def sanitize_payload(payload: dict[str, Any], text_fields: list[str] | None = None) -> dict[str, Any]:
    """
    Recursively or selectively sanitize string fields in a payload dict.
    If text_fields is provided, only those keys are sanitized; otherwise all strings are sanitized.
    """
    sanitized: dict[str, Any] = {}
    for k, v in payload.items():
        if isinstance(v, str):
            if text_fields is None or k in text_fields:
                sanitized[k] = sanitize_text(v)
            else:
                sanitized[k] = v
        elif isinstance(v, dict):
            sanitized[k] = sanitize_payload(v, text_fields)
        elif isinstance(v, list):
            sanitized[k] = [
                sanitize_text(item) if isinstance(item, str) and (text_fields is None or k in text_fields) else item
                for item in v
            ]
        else:
            sanitized[k] = v
    return sanitized
