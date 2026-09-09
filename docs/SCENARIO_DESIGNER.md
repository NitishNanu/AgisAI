# 🛠️ AegisAI — Scenario Designer & Management Engine

The **Scenario Designer** is an enterprise-grade simulation blueprint studio that enables emergency commanders, researchers, and dispatchers to visually configure, validate, preview, and execute reproducible disaster simulations.

---

## 1. Scenario Lifecycle & State Machine

Every disaster scenario transitions through an explicit, deterministic state machine:

```text
[ DRAFT ] ──────────► [ VALIDATING ] ──────────► [ READY ]
                           │                        │
                           ▼                        ▼
                       [ FAILED ]              [ RUNNING ] ◄──► [ PAUSED ]
                                                    │
                                                    ▼
                                               [ COMPLETED ]
                                                    │
                                                    ▼
                                               [ ARCHIVED ]
```

### Supported States:
- `DRAFT`: Initial in-progress scenario configuration.
- `VALIDATING`: Semantic boundary and geographic check execution.
- `READY`: Validated blueprint saved in database with unique UUID and deterministic seed.
- `RUNNING`: Actively driving the authoritative Digital Twin simulation engine.
- `PAUSED`: Simulation clock temporarily halted; city state preserved.
- `COMPLETED`: Simulation run duration completed; final snapshot and metrics archived.
- `FAILED`: Execution halted due to critical error.
- `ARCHIVED`: Soft-deleted blueprint removed from active list but retained for historical audits.

---

## 2. Multi-Factor Baseline Risk Scorer

The `BaselineRiskScorer` executes a transparent analytical model combining:

1. **Hazard Severity Multiplier**: `LOW` (0.2), `MODERATE` (0.4), `HIGH` (0.7), `SEVERE` (0.85), `CRITICAL` (1.0).
2. **Exposed Population Density**: Calculates residential exposure within the blast / flood / seismic impact radius.
3. **Vulnerable Population Share**: Modulates projected casualty rates for elderly, children, and mobility-limited demographics.
4. **Lifeline Infrastructure Disruption**: Computes road damage, bridge impassability, and power grid outage penalties.
5. **Medical & Shelter Surge Pressure**: Evaluates hospital bed deficits and evacuation shelter capacity.
6. **Resource Coverage Ratio**: Ratios available ambulances, fire trucks, and rescue teams against demand.

---

## 3. Standardized Scenario Presets Catalog

The system provides ready-to-run presets:

| Preset Name | Hazard Type | Severity | Default Epicenter | Key Characteristics |
| :--- | :--- | :--- | :--- | :--- |
| **Major Urban Earthquake (M7.2)** | `EARTHQUAKE` | `SEVERE` | 30.7399, 76.7830 | Structural collapse in Sector 17 commercial core, road damage, high casualty risk. |
| **Monsoon Flash Flood** | `FLOOD` | `HIGH` | 30.7150, 76.7600 | Heavy precipitation, waterlogged transport corridors, mass shelter surge. |
| **Industrial Chemical Fire & Hazmat** | `FIRE` | `CRITICAL` | 30.7150, 76.7600 | Toxic plume dispersion, downwind evacuation, high medical trauma demand. |

---

## 4. REST API Endpoint Specification

### `POST /api/v1/scenarios`
- **Auth**: `ADMIN`, `COMMANDER`, `DISPATCHER`
- **Request Body**: Complete `ScenarioCreateRequest` JSON payload.
- **Response**: `ApiResponse[ScenarioResponse]` with UUID.

### `POST /api/v1/scenarios/validate`
- **Auth**: Authenticated User
- **Response**: `ApiResponse[ScenarioValidateResponse]` with detailed error list.

### `POST /api/v1/scenarios/preview`
- **Auth**: Authenticated User
- **Response**: `ApiResponse[ScenarioPreviewResponse]` with casualty ranges, bed demand, risk score, and risk factors.

### `POST /api/v1/scenarios/{id}/clone`
- **Auth**: `ADMIN`, `COMMANDER`, `DISPATCHER`
- **Description**: Duplicates scenario configuration under a new UUID for parameter branching and What-If comparison.

### `POST /api/v1/scenarios/{id}/launch`
- **Auth**: `ADMIN`, `COMMANDER`, `DISPATCHER`
- **Workflow**:
  1. Configures `DigitalTwinEngine` with scenario environment, weather, and disaster parameters.
  2. Creates `ScenarioRun` record with initial city state snapshot.
  3. Starts simulation engine.
  4. Emits `SCENARIO_LAUNCHED` event to connected WebSocket clients.
