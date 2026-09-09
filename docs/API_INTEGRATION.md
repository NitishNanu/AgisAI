# 📡 AegisAI — API Integration Specification

This document details the standardized REST API contracts between the FastAPI backend and React frontend.

---

## 1. Authentication & Identity Management

### `POST /api/v1/auth/login`
- **Method**: `POST`
- **Auth**: Public / Rate-limited (20/min)
- **Request Body (JSON)**:
  ```json
  {
    "email": "commander@aegis.local",
    "password": "Password123!"
  }
  ```
- **Response (`ApiResponse[TokenResponse]`)**:
  ```json
  {
    "success": true,
    "status_code": 200,
    "message": "Login successful.",
    "data": {
      "access_token": "eyJhbGciOi...",
      "refresh_token": "eyJhbGciOi...",
      "token_type": "bearer",
      "user_id": 1,
      "email": "commander@aegis.local",
      "role": "COMMANDER",
      "expires_in_minutes": 60
    }
  }
  ```

### `POST /api/v1/auth/refresh`
- **Method**: `POST`
- **Auth**: Public
- **Request Body**:
  ```json
  {
    "refresh_token": "eyJhbGciOi..."
  }
  ```
- **Response**: Returns renewed `TokenResponse` pair.

### `GET /api/v1/auth/me`
- **Method**: `GET`
- **Auth**: Bearer Token required
- **Response (`ApiResponse[UserProfileResponse]`)**:
  ```json
  {
    "success": true,
    "status_code": 200,
    "message": "Profile retrieved successfully.",
    "data": {
      "id": 1,
      "name": "Commander Alpha",
      "email": "commander@aegis.local",
      "role": "COMMANDER",
      "is_active": true,
      "created_at": "2026-08-20T10:00:00Z",
      "updated_at": "2026-08-20T10:00:00Z"
    }
  }
  ```

---

## 2. Incident & Disaster Management

### `GET /api/v1/incidents`
- **Method**: `GET`
- **Query Parameters**:
  - `page` (int, default: 1)
  - `page_size` (int, default: 50)
  - `status` (string, optional: `ACTIVE`, `CONTAINED`, `RESOLVED`)
  - `type` (string, optional: `FIRE`, `FLOOD`, `EARTHQUAKE`, etc.)
  - `severity` (string, optional: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- **Response (`ApiResponse.paginated`)**:
  ```json
  {
    "success": true,
    "status_code": 200,
    "message": "Retrieved 6 incidents.",
    "data": {
      "items": [
        {
          "id": 1,
          "title": "Industrial Chemical Fire - Docklands",
          "disaster_type": "FIRE",
          "severity": "CRITICAL",
          "status": "ACTIVE",
          "latitude": 37.7749,
          "longitude": -122.4194,
          "created_at": "2026-09-01T12:00:00Z"
        }
      ],
      "total": 6,
      "page": 1,
      "page_size": 50,
      "pages": 1
    }
  }
  ```

### `GET /api/v1/incidents/{id}/recommended-teams`
- **Method**: `GET`
- **Query Parameters**: `limit` (int, default: 5)
- **Response**:
  ```json
  {
    "success": true,
    "status_code": 200,
    "data": {
      "disaster_id": 1,
      "recommended": {
        "team_id": 2,
        "team_name": "Hazmat Heavy Response 4",
        "vehicle_type": "HAZMAT_TRUCK",
        "members": 6,
        "status": "AVAILABLE",
        "distance_km": 4.2,
        "eta_minutes": 8.5,
        "score": 94.2,
        "route_geometry": { ... }
      },
      "all_teams": [ ... ],
      "reason": "Optimal vehicle capability match and shortest transit ETA."
    }
  }
  ```

---

## 3. Mission & Resource Assignments

### `POST /api/v1/assignments`
- **Method**: `POST`
- **Auth**: `ADMIN`, `COMMANDER`, `DISPATCHER`
- **Request Body**:
  ```json
  {
    "incident_id": 1,
    "team_id": 2,
    "notes": "Immediate deployment to chemical sector A."
  }
  ```
- **Response**: `ApiResponse[AssignmentResponse]` with state `ASSIGNED` / `DISPATCHED`.

### `PUT /api/v1/assignments/{id}/status`
- **Method**: `PUT`
- **Auth**: `ADMIN`, `COMMANDER`, `DISPATCHER`, `RESPONDER`
- **Request Body**:
  ```json
  {
    "status": "EN_ROUTE"
  }
  ```
- **Lifecycle Sequence**: `ASSIGNED` ➔ `DISPATCHED` ➔ `EN_ROUTE` ➔ `ARRIVED` ➔ `COMPLETED`.

### `GET /api/v1/missions`
- **Method**: `GET`
- **Query Parameters**: `active_only` (bool, default: false)
- **Response**: Returns aggregated nested payload with disaster, team, live ETA, and route geometry.

---

## 4. Facilities & Resources

### `GET /api/v1/hospitals`
- **Method**: `GET`
- **Response**: List of hospitals including total beds, available beds, ICU occupancy, and ER capacity.

### `GET /api/v1/resources/shelters`
- **Method**: `GET`
- **Response**: List of shelters with max capacity, current occupants, and pet-friendly flags.

### `GET /api/v1/resources/teams`
- **Method**: `GET`
- **Response**: List of rescue teams with vehicle equipment, crew size, and availability status.
