# 🛡️ AegisAI — Emergency Response & Digital Twin Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3.1-61DAFB.svg?style=flat&logo=React&logoColor=black)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg?style=flat&logo=PostgreSQL&logoColor=white)](https://www.postgresql.org)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4-5B8A3C.svg?style=flat&logo=PostgreSQL&logoColor=white)](https://postgis.net)
[![OSRM](https://img.shields.io/badge/OSRM-Routing-008080.svg?style=flat&logo=OpenStreetMap&logoColor=white)](https://project-osrm.org)
[![Ollama](https://img.shields.io/badge/Ollama-Llama_3.2-black.svg?style=flat)](https://ollama.com)

**AegisAI** is a mission-critical emergency response, resource allocation, and digital-twin disaster simulation platform. It integrates geospatial intelligence (PostGIS + OSRM), deterministic AI decision optimization (Kuhn-Munkres bipartite matching + multi-criteria scoring), Explainable AI (XAI) operational briefings (Ollama Llama 3.2), real-time mission tracking, multi-horizon predictive forecasting (+5m, +15m, +30m, +60m), and facility saturation monitoring into a unified command and control system.

---

## 📌 Implementation Status Matrix

| Priority / Module | Backend Status | Frontend Status | Overall Status | Notes & Capabilities |
| :--- | :---: | :---: | :---: | :--- |
| **Priority 1: Frontend ↔ Backend Integration** | ✅ Complete | ✅ Complete | **DONE** | Full JWT lifecycle, 6-role RBAC, AuthModal, REST endpoints, and WebSocket sync. |
| **Priority 2: Digital Twin EOC UI** | ✅ Complete | ✅ Complete | **DONE** | Palantir-style EOC command center, real-time tick engine, map layers, live HUD, and event ring buffer. |
| **Priority 3: Scenario Designer & Studio** | ✅ Complete | ✅ Complete | **DONE** | Disaster blueprint designer, multi-hazard presets, parameter overrides, and live injection. |
| **Priority 4: AI Decision Intelligence Engine** | ✅ Complete | ✅ Complete | **DONE** | Global Kuhn-Munkres optimization, hard constraints, multi-criteria scoring, XAI briefings, human approval, and transaction-safe dispatch. |
| **Priority 5: Predictive AI Dashboard** | ✅ Complete | ✅ Complete | **DONE** | Multi-horizon (+5m, +15m, +30m, +60m) forecasting for casualties, hospital ICU overload, fleet shortages, risk envelopes, and proactive alerts. |
| **Incident Management** | ✅ Complete | ✅ Complete | **DONE** | Spatial indexing, severity tagging, interactive Leaflet map markers, and radius visualization. |
| **Live OSRM Routing** | ✅ Complete | ✅ Complete | **DONE** | Turn-by-turn road network routing via OSRM with Haversine fallback; GeoJSON polyline rendering. |
| **Mission Control Tracking** | ✅ Complete | ✅ Complete | **DONE** | State machine lifecycle (`ASSIGNED` ➔ `DISPATCHED` ➔ `EN_ROUTE` ➔ `ARRIVED` ➔ `COMPLETED`). |
| **Hospitals & Medical Capacity** | ✅ Complete | ✅ Complete | **DONE** | Emergency ER capacity, total beds, ICU occupancy, operational status, proximity queries. |
| **Shelters & Evacuation Centers** | ✅ Complete | ✅ Complete | **DONE** | Shelter capacity, current occupancy, supply tracking, pet friendliness, spatial proximity. |
| **Predictive AI (Ollama LLM)** | ✅ Complete | ✅ Complete | **DONE** | Llama 3.2 casualty & spread forecasting + Explainable AI tactical briefings. |
| **Analytics & System Health** | ✅ Complete | ✅ Complete | **DONE** | Policy benchmarking, KPI aggregation, health scoring, and What-If comparison. |
| **RabbitMQ Event Bus** | ✅ Complete | N/A | **DONE** | Async event broker integration for background simulation and decision publishing. |

---

## 🔮 Priority 5: Predictive AI Dashboard & Forecasting Intelligence

The **Predictive Intelligence Layer** translates live disaster telemetry and simulation state into actionable multi-horizon projections across **+5m, +15m, +30m, and +60m** horizons.

### Architecture
```text
                    DIGITAL TWIN
                         │
                         ▼
                  CURRENT STATE
                         │
                         ▼
              ┌─────────────────────┐
              │ Prediction Engine   │
              └──────────┬──────────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
   Casualty         Hospital Load      Resource Demand
   Prediction       Prediction         Prediction
        │                │                 │
        └────────────────┼─────────────────┘
                         ▼
                 Risk Aggregation
                         │
                         ▼
                Predictive Analytics
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        REST API                WebSocket
              │                     │
              └──────────┬──────────┘
                         ▼
                 COMMAND DASHBOARD
```

### Key Forecasting Domains:
1. **Casualty Horizon Forecasting**: Mathematical logarithmic/exponential patient surge curves accounting for hazard velocity, weather severity multipliers, and active rescue team mitigation.
2. **Hospital ER & ICU Saturation**: Projections of bed and ICU occupancy % across facilities, estimating exact expected overload timestamps (`expected_overload_minutes`).
3. **Resource Demand & Fleet Shortages**: Real-time fleet deficit forecasting for Ambulances, Fire Engines, Rescue Boats, Police Patrols, and Drones.
4. **Spatial Disaster Risk & Fire Spread Envelopes**: Multi-horizon concentric propagation envelopes (+0m, +5m, +15m, +30m, +60m) rendered dynamically on Leaflet maps.
5. **Predictive Alerts HUD**: Proactive alerts for impending ICU saturation, resource deficits, and rapid hazard expansion with deduplication cooldowns and factual XAI explanations.
6. **Prediction Records & Error Tracking**: Database-backed audit logging (`prediction_records`) for tracking actual observed outcomes vs forecasts (MAE / MAPE accuracy evaluation).

---

## 🧠 Priority 4: AI Decision Intelligence Engine

The **AI Decision Engine** determines the mathematically optimal emergency response action given the disaster state, available resources, hospital capacities, weather, and road conditions.

### Architectural Pipeline
```text
       ┌───────────────────────────────┐
       │   Digital Twin / DB State     │
       │ (Incidents, Units, Hospitals) │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │   AI State Aggregator (DTO)   │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │      Prediction Layer         │
       │ (Spread, Casualties, Demand)  │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │     Candidate Generator       │
       │  (Route & ETA via OSRM)       │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │     Constraint Engine         │
       │ (Hard Constraints / Filters)  │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │   Scoring & Optimization      │
       │ (Normalized Criteria / Solver)│
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │     Explainability Engine     │
       │ (Structured XAI + Ollama LLM) │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │   Human Commander Approval    │
       │ (Approve / Reject / Modify)   │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │   Transaction-Safe Execution  │
       │ (AssignmentService + Locking) │
       └───────────────┬───────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │ Real-Time WebSocket & Monitor │
       └───────────────────────────────┘
```

---

## 🏗️ Architecture & Technology Stack

### Core Technologies:
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10 compatible) with Pydantic v2 and SQLAlchemy 2.0.
- **Database**: PostgreSQL 15 + [PostGIS](https://postgis.net/) Extension (`ST_DWithin`, `ST_Distance`).
- **Optimization & Math**: NumPy vectorized Kuhn-Munkres bipartite matching solver.
- **Routing Engine**: [OSRM](https://project-osrm.org/) API with automatic road-factored Haversine fallback.
- **AI / LLM Engine**: [Ollama](https://ollama.com/) running `llama3.2:3b` for operational briefings.
- **Frontend**: [React 18/19](https://reactjs.org/), [Vite](https://vitejs.dev/), [Leaflet](https://leafletjs.com/), Custom responsive SVG charts & Glassmorphism Design System.
- **Task Scheduling**: APScheduler for Digital Twin simulation ticks.
- **Caching & Messaging**: Redis 7 and RabbitMQ 3.

---

## 📂 Project Structure

```text
GoogleMapsDisaster/
├── backend/
│   ├── alembic/
│   │   └── versions/
│   │       ├── 001_initial_schema.py           # Core tables migration
│   │       ├── 002_ai_decision_engine.py       # AI decisions, candidates, feedback, events
│   │       └── 003_prediction_intelligence.py   # Prediction records and forecast history
│   ├── app/
│   │   ├── api/
│   │   │   ├── router.py                       # Aggregated API router (includes /predictions & /ai)
│   │   │   └── routes/                         # Domain route handlers
│   │   ├── core/
│   │   │   ├── config/settings.py              # Pydantic v2 application configuration
│   │   │   ├── database/session.py             # SQLAlchemy engine & session maker
│   │   │   ├── middleware/                     # Error handling & rate limiting
│   │   │   ├── security/jwt.py                 # JWT token lifecycle & RBAC
│   │   │   └── websocket/manager.py            # Live WebSocket connection manager
│   │   ├── modules/
│   │   │   ├── prediction/                     # Priority 5: Predictive AI Dashboard & Forecaster
│   │   │   │   ├── forecaster.py               # TimeHorizonForecaster (+5m, +15m, +30m, +60m)
│   │   │   │   ├── alerts.py                   # PredictiveAlertEngine with deduplication & XAI
│   │   │   │   ├── models.py                   # PredictionRecord ORM entity
│   │   │   │   ├── schemas.py, service.py, router.py, ai_client.py
│   │   │   │   └── tests/                      # Forecaster, alert, and service unit tests
│   │   │   ├── ai/                             # Priority 4: AI Decision Intelligence Layer
│   │   │   ├── analytics/                      # KPI aggregation & health reports
│   │   │   ├── auth/                           # Authentication & user management
│   │   │   ├── hospital/                       # Hospital facilities & bed/ICU tracking
│   │   │   ├── incident/                       # Incident management & spatial query service
│   │   │   ├── resource/                       # Rescue units, shelters & assignments
│   │   │   ├── scenario/                       # Scenario designer studio
│   │   │   └── simulation/                     # Digital Twin simulator & What-If sandbox
│   │   ├── routing/osrm.py                     # OSRM road routing client
│   │   └── services/assignment_service.py      # Transaction-safe dispatch with SELECT FOR UPDATE
│   ├── seed.py                                 # Master database seeding script
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Prediction/
│   │   │   │   └── PredictiveDashboard.jsx     # Command-Center Forecasting HUD & SVG Charts
│   │   │   ├── Map/DisasterMap.jsx             # Leaflet Multi-Layer Map with hazard envelopes
│   │   │   ├── Layout/, Disaster/, Scenario/, Simulation/
│   │   ├── pages/Dashboard.jsx                 # Unified EOC Command Dashboard
│   │   ├── services/
│   │   │   ├── predictionService.js            # Frontend client for predictive endpoints
│   │   │   ├── aiDecisionService.js            # Frontend client for AI Decision Engine
│   │   │   └── api.js                          # Axios HTTP client with auth interceptors
│   │   └── index.css                           # Glassmorphism Design System & chart styles
│   └── package.json
│
├── docker-compose.yml                          # Multi-container orchestration
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Python**: `3.10`
- **Node.js**: `v18+` or `v20+`
- **PostgreSQL**: `15+` with `PostGIS` extension.
- **Ollama**: (Optional) running `llama3.2:3b`.

---

### 1. Database Setup
Create a PostgreSQL database named `aegisai_db` (or `rescuenet`):
```sql
CREATE DATABASE aegisai_db;
\c aegisai_db
CREATE EXTENSION IF NOT EXISTS postgis;
```

---

### 2. Backend Setup

1. **Activate Python environment & install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Apply Alembic Migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Seed the database**:
   ```bash
   python seed.py
   ```

4. **Start FastAPI Backend**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - Interactive Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Alternative ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 3. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   - Access the dashboard at [http://localhost:5173](http://localhost:5173)

---

## 📡 REST API Reference Summary

### 🔮 Predictive AI & Forecasting Intelligence (`/api/v1/predictions`)

| Method | Endpoint | Description | Auth / Role |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/predictions/dashboard` | Consolidated multi-horizon predictive dashboard payload | Authenticated |
| `GET` | `/api/v1/predictions/casualties` | Multi-horizon (+5m, +15m, +30m, +60m) casualty surge forecast | Authenticated |
| `GET` | `/api/v1/predictions/hospitals` | Hospital bed & ICU capacity saturation forecast | Authenticated |
| `GET` | `/api/v1/predictions/resources` | Emergency fleet demand and shortage forecast | Authenticated |
| `GET` | `/api/v1/predictions/disaster-risk`| Multi-hazard spatial risk and propagation forecast | Authenticated |
| `GET` | `/api/v1/predictions/fire-spread` | Multi-horizon fire propagation envelopes | Authenticated |
| `GET` | `/api/v1/predictions/flood-risk` | Flood inundation and evacuation urgency forecast | Authenticated |
| `GET` | `/api/v1/predictions/history` | Historical prediction records and telemetry | Authenticated |
| `POST` | `/api/v1/predictions/history/{id}/outcome` | Record observed outcome for error tracking (MAE / MAPE) | `ADMIN`, `COMMANDER` |
| `POST` | `/api/v1/predictions/spread` | Disaster spread radius prediction with Ollama XAI | Authenticated |
| `POST` | `/api/v1/predictions/optimize` | AI-driven greedy resource allocation optimization | `ADMIN`, `COMMANDER` |
| `POST` | `/api/v1/predictions/recommend` | RL-based action recommendation | `ADMIN`, `COMMANDER`, `DISPATCHER` |
| `POST` | `/api/v1/predictions/explain` | XAI decision explainability narrative | Authenticated |

### 🧠 AI Decision Intelligence Engine (`/api/v1/ai`)

| Method | Endpoint | Description | Auth / Role |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/ai/decisions/generate` | Generate AI emergency response recommendations | `ADMIN`, `COMMANDER`, `DISPATCHER` |
| `GET` | `/api/v1/ai/decisions` | List and filter decisions (paginated) | Authenticated |
| `GET` | `/api/v1/ai/decisions/{id}` | Get decision details by ID or UUID | Authenticated |
| `POST` | `/api/v1/ai/decisions/{id}/approve` | Approve decision (auto-execute dispatch if requested) | `ADMIN`, `COMMANDER`, `DISPATCHER` |
| `POST` | `/api/v1/ai/decisions/{id}/reject` | Reject recommendation with commander reason | `ADMIN`, `COMMANDER`, `DISPATCHER` |
| `POST` | `/api/v1/ai/decisions/{id}/modify` | Override resource unit or hospital destination | `ADMIN`, `COMMANDER`, `DISPATCHER` |
| `POST` | `/api/v1/ai/decisions/{id}/execute` | Execute approved decision (transaction-safe dispatch) | `ADMIN`, `COMMANDER`, `DISPATCHER` |
| `GET` | `/api/v1/ai/decisions/{id}/explanation` | Get LLM tactical briefing & XAI reasoning | Authenticated |
| `POST` | `/api/v1/ai/decisions/benchmark` | Benchmark Baseline vs Heuristic vs Optimized vs ML | `ADMIN`, `COMMANDER` |
| `POST` | `/api/v1/ai/decisions/what-if` | Run What-If simulation on isolated state | `ADMIN`, `COMMANDER` |
| `POST` | `/api/v1/ai/decisions/{id}/feedback` | Record commander feedback & observed outcomes | `ADMIN`, `COMMANDER`, `DISPATCHER` |

---

## 🧪 Testing Suite & Quality Assurance

Run the test suite:
```bash
pytest backend/app/modules/prediction/tests backend/app/modules/ai/tests -v
```

---

## 📄 License
This project is licensed under the MIT License.
