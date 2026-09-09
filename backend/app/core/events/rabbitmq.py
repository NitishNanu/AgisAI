"""
AegisAI Core — RabbitMQ Event Bus Publisher.

Provides asynchronous, non-blocking publishing of domain events (e.g. incident updates,
resource dispatches, simulation ticks) to RabbitMQ via aio-pika.
Falls back gracefully if RabbitMQ is not available or offline.
"""

import json
from typing import Any

import structlog

from app.core.config.settings import settings

logger = structlog.get_logger("aegis_ai.core.events.rabbitmq")

_connection: Any = None
_channel: Any = None
_exchange: Any = None


def get_rabbitmq_url() -> str:
    """Construct RabbitMQ connection URL from settings."""
    user = settings.RABBITMQ_USER
    password = settings.RABBITMQ_PASSWORD
    host = settings.RABBITMQ_HOST
    port = settings.RABBITMQ_PORT
    vhost = settings.RABBITMQ_VHOST.lstrip("/")
    return f"amqp://{user}:{password}@{host}:{port}/{vhost}"


async def get_exchange() -> Any:
    """Lazily initialize connection, channel, and topic exchange."""
    global _connection, _channel, _exchange

    if _exchange is not None and not _channel.is_closed:
        return _exchange

    try:
        import aio_pika

        _connection = await aio_pika.connect_robust(
            get_rabbitmq_url(),
            timeout=2.0,
        )
        _channel = await _connection.channel()
        _exchange = await _channel.declare_exchange(
            name=settings.RABBITMQ_EXCHANGE,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        logger.info("rabbitmq_connected", exchange=settings.RABBITMQ_EXCHANGE)
        return _exchange
    except Exception as exc:
        logger.warning("rabbitmq_connection_failed_degraded", error=str(exc))
        _exchange = None
        return None


async def publish_event(routing_key: str, payload: dict[str, Any]) -> bool:
    """
    Publish an event message to RabbitMQ exchange.
    Returns True if successfully delivered to exchange, False otherwise.
    Never throws an exception so callers are not blocked.
    """
    try:
        exchange = await get_exchange()
        if exchange is None:
            return False

        import aio_pika

        body = json.dumps(payload, default=str).encode("utf-8")
        message = aio_pika.Message(
            body=body,
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=routing_key)
        logger.debug("rabbitmq_event_published", routing_key=routing_key)
        return True
    except Exception as exc:
        logger.warning("rabbitmq_publish_error", routing_key=routing_key, error=str(exc))
        return False


async def close_rabbitmq() -> None:
    """Cleanly close RabbitMQ connection on application shutdown."""
    global _connection, _channel, _exchange
    try:
        if _channel and not _channel.is_closed:
            await _channel.close()
        if _connection and not _connection.is_closed:
            await _connection.close()
    except Exception as exc:
        logger.debug("rabbitmq_close_error", error=str(exc))
    finally:
        _channel = None
        _connection = None
        _exchange = None
