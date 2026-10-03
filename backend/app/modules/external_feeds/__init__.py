"""
External feeds module entrypoint.
"""
from app.modules.external_feeds.service import feeds_service
from app.modules.external_feeds.router import router

__all__ = ["feeds_service", "router"]
