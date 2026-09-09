import uuid
from typing import Any
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
import structlog
from jose import JWTError

from app.core.config.settings import settings
from app.core.websocket.manager import ws_manager

logger = structlog.get_logger("aegis_ai.api.websocket")

router = APIRouter(tags=["Real-time Telemetry WebSocket"])

# WebSocket close codes
_WS_POLICY_VIOLATION = 1008  # Used for auth failures


def _validate_ws_token(token: str | None) -> dict[str, Any] | None:
    """
    Decode and validate a JWT token for WebSocket authentication.

    Returns the decoded payload on success, or None if the token is
    missing / invalid / expired. Deliberately does NOT raise — the caller
    decides how to handle the failure so the WebSocket handshake can be
    rejected cleanly.
    """
    if not token or token.strip() in ("", "null", "undefined", "None"):
        return None
    try:
        from jose import jwt  # noqa: PLC0415

        payload: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("type") != "access":
            return None
        if not payload.get("sub"):
            return None
        return payload
    except JWTError:
        return None


@router.websocket("/ws/v1/stream")
async def websocket_stream_endpoint(
    websocket: WebSocket,
    client_id: str | None = Query(default=None),
    token: str | None = Query(default=None),
) -> None:
    # ------------------------------------------------------------------ #
    # C3 FIX: Authenticate the token BEFORE accepting the WebSocket.      #
    # Reject unauthenticated connections with code 1008 (Policy Violation) #
    # ------------------------------------------------------------------ #
    payload = _validate_ws_token(token)
    if payload is None:
        logger.warning(
            "websocket_auth_rejected",
            client_id=client_id,
            reason="missing_or_invalid_token",
        )
        await websocket.close(code=_WS_POLICY_VIOLATION, reason="Authentication required.")
        return

    user_id = payload.get("sub")
    user_role = payload.get("role", "CITIZEN")

    assigned_client_id = client_id or str(uuid.uuid4())
    await ws_manager.connect(assigned_client_id, websocket)

    await ws_manager.send_personal_message(
        assigned_client_id,
        {
            "event": "connection_established",
            "client_id": assigned_client_id,
            "user_id": user_id,
            "role": user_role,
            "channels": ["simulation", "missions", "incidents", "all"],
            "message": "Connected to AegisAI Live Telemetry Stream.",
        },
    )

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "subscribe":
                channel = data.get("channel", "all")
                ws_manager.subscribe(assigned_client_id, channel)
                await ws_manager.send_personal_message(
                    assigned_client_id,
                    {"event": "subscription_confirmed", "channel": channel},
                )

            elif action == "unsubscribe":
                channel = data.get("channel")
                if channel:
                    ws_manager.unsubscribe(assigned_client_id, channel)
                    await ws_manager.send_personal_message(
                        assigned_client_id,
                        {"event": "unsubscription_confirmed", "channel": channel},
                    )

            elif action == "ping":
                await ws_manager.send_personal_message(
                    assigned_client_id,
                    {"event": "pong", "timestamp": data.get("timestamp")},
                )

    except WebSocketDisconnect:
        ws_manager.disconnect(assigned_client_id)
    except Exception as e:
        logger.warning("websocket_session_error", client_id=assigned_client_id, error=str(e))
        ws_manager.disconnect(assigned_client_id)

