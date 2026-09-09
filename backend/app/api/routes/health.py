"""
AegisAI Health Check — Service Readiness Probe.

Exposes GET /api/v1/health for load balancers and monitoring systems.
Checks connectivity to all critical downstream dependencies:
  - PostgreSQL (via SQLAlchemy engine ping)
  - Redis (via direct PING command)
  - RabbitMQ (via TCP socket connect to broker port)

Returns per-service status so degraded states can be diagnosed precisely.
HTTP 200 is always returned — consumers must inspect `data.status`.
"""

import socket
import time
from typing import Any

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.common.response import ApiResponse
from app.core.config.settings import settings
from app.core.database.session import get_db

logger = structlog.get_logger("aegis_ai.health")

router = APIRouter(prefix="/health", tags=["Platform Health"])


def _check_postgres(db: Session) -> dict[str, Any]:
    """Ping PostgreSQL by executing SELECT 1 via the active session."""
    try:
        start = time.perf_counter()
        db.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("health_postgres_failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


def _check_redis() -> dict[str, Any]:
    """Ping Redis using the synchronous redis client."""
    try:
        import redis as redis_lib

        start = time.perf_counter()
        client = redis_lib.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("health_redis_failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


def _check_rabbitmq() -> dict[str, Any]:
    """
    Check RabbitMQ availability via TCP socket connect.

    A TCP connect to the broker port is sufficient for a liveness check
    without opening a full AMQP channel in a synchronous context.
    """
    try:
        start = time.perf_counter()
        sock = socket.create_connection(
            (settings.RABBITMQ_HOST, settings.RABBITMQ_PORT),
            timeout=2,
        )
        sock.close()
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {"status": "healthy", "latency_ms": latency_ms}
    except Exception as exc:
        logger.warning("health_rabbitmq_failed", error=str(exc))
        return {"status": "unhealthy", "error": str(exc)}


@router.get(
    "",
    response_model=ApiResponse[dict],
    summary="Platform health check — all downstream dependencies",
    description=(
        "Returns HTTP 200 in all cases (healthy or degraded) so that "
        "load balancers continue routing traffic. Inspect `data.status` "
        "to determine overall health. Individual service checks are "
        "included under `data.services`."
    ),
)
def health_check(
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """
    Liveness and readiness probe for AegisAI platform.

    Checks:
      - PostgreSQL: SELECT 1 via active SQLAlchemy session
      - Redis: PING via synchronous redis client
      - RabbitMQ: TCP connect to broker port
    """
    postgres_result = _check_postgres(db)
    redis_result = _check_redis()
    rabbitmq_result = _check_rabbitmq()

    all_healthy = all(
        svc.get("status") == "healthy"
        for svc in [postgres_result, redis_result, rabbitmq_result]
    )
    overall = "healthy" if all_healthy else "degraded"

    logger.info(
        "health_check",
        status=overall,
        postgres=postgres_result.get("status"),
        redis=redis_result.get("status"),
        rabbitmq=rabbitmq_result.get("status"),
    )

    return ApiResponse.ok(
        data={
            "status": overall,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "services": {
                "postgres": postgres_result,
                "redis": redis_result,
                "rabbitmq": rabbitmq_result,
            },
        },
        message=f"Platform is {overall}.",
    )
