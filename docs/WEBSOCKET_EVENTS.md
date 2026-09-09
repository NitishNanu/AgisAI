# ⚡ AegisAI — Real-Time WebSocket Protocol Specification

WebSocket Endpoint: `ws://localhost:8000/ws/v1/stream` (Optional query param: `?token=<JWT_ACCESS_TOKEN>`)

---

## 1. Connection Lifecycle & Handshake

### Client Connects
Upon connection, server replies with `connection_established`:
```json
{
  "event": "connection_established",
  "client_id": "c73a4b91-...",
  "channels": ["simulation", "missions", "incidents", "all"],
  "message": "Connected to AegisAI Live Telemetry Stream."
}
```

### Channel Subscription
Client can subscribe/unsubscribe to telemetry channels:
```json
{
  "action": "subscribe",
  "channel": "incidents"
}
```

Server confirmation:
```json
{
  "event": "subscription_confirmed",
  "channel": "incidents"
}
```

### Keepalive Heartbeat
Every 25 seconds, client sends ping:
```json
{
  "action": "ping",
  "timestamp": 1756730000000
}
```
Server responds with `pong`:
```json
{
  "event": "pong",
  "timestamp": 1756730000000
}
```

---

## 2. Real-Time Telemetry Event Catalog

### `INCIDENT_CREATED`
- **Channel**: `incidents` | `all`
- **Trigger**: New emergency reported via `POST /api/v1/incidents`.
- **Payload**:
  ```json
  {
    "event": "INCIDENT_CREATED",
    "channel": "incidents",
    "timestamp": "2026-09-01T12:30:00Z",
    "data": {
      "id": 7,
      "title": "Flash Flood - Lowland Valley",
      "disaster_type": "FLOOD",
      "severity": "HIGH",
      "status": "ACTIVE",
      "latitude": 37.7812,
      "longitude": -122.4298,
      "affected_radius_meters": 1500,
      "estimated_affected_people": 450,
      "created_at": "2026-09-01T12:30:00Z"
    }
  }
  ```
- **Frontend Action**: Incremental prepend to `disasters` list, renders new pulsating marker on Leaflet map.

### `INCIDENT_UPDATED`
- **Channel**: `incidents` | `all`
- **Trigger**: Incident modified via `PUT /api/v1/incidents/{id}` (e.g. status changed from `ACTIVE` to `CONTAINED`).
- **Payload**: Contains updated fields (`status`, `severity`, etc.).
- **Frontend Action**: Updates matching incident card, badge, and map popup.

### `MISSION_CREATED`
- **Channel**: `missions` | `all`
- **Trigger**: Rescue team dispatched via `POST /api/v1/assignments`.
- **Payload**: Complete assignment record with `assignment_id`, `team_id`, `incident_id`, `status`.
- **Frontend Action**: Updates team status to `DISPATCHED`, renders live mission card in Mission Control HUD, plots OSRM polyline.

### `MISSION_UPDATED`
- **Channel**: `missions` | `all`
- **Trigger**: Mission status advanced (`ASSIGNED` ➔ `DISPATCHED` ➔ `EN_ROUTE` ➔ `ARRIVED` ➔ `COMPLETED`).
- **Payload**:
  ```json
  {
    "event": "MISSION_UPDATED",
    "channel": "missions",
    "timestamp": "2026-09-01T12:35:00Z",
    "data": {
      "assignment_id": 4,
      "status": "ARRIVED",
      "team_id": 2,
      "incident_id": 1,
      "started_at": "2026-09-01T12:32:00Z",
      "completed_at": null
    }
  }
  ```
- **Frontend Action**: Updates mission status badge in real-time, marks team as available upon completion.

### `SIMULATION_TICK`
- **Channel**: `simulation` | `all`
- **Trigger**: Digital Twin engine tick step.
- **Payload**: Dynamic virtual city state with updated weather, traffic congestion index, and damage progression.
