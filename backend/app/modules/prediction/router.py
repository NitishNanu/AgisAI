"""
AegisAI Prediction Module — API Router.

Provides predictive dashboard endpoints, time-horizon forecasts, and AI/ML algorithms:
- GET  /api/v1/predictions/dashboard     — Consolidated command-center predictive dashboard
- GET  /api/v1/predictions/casualties    — Multi-horizon casualty forecast
- GET  /api/v1/predictions/hospitals     — Hospital capacity & ICU saturation forecast
- GET  /api/v1/predictions/resources     — Resource fleet demand forecast
- GET  /api/v1/predictions/disaster-risk — Multi-hazard spatial risk forecast
- GET  /api/v1/predictions/fire-spread   — Fire spread propagation zones
- GET  /api/v1/predictions/flood-risk    — Flood risk and evacuation urgency
- GET  /api/v1/predictions/history       — Historical prediction records
- POST /api/v1/predictions/history/{id}/outcome — Record actual outcome for error tracking
- POST /api/v1/predictions/spread        — Disaster spread radius prediction
- POST /api/v1/predictions/optimize      — Resource allocation optimization
- POST /api/v1/predictions/recommend     — RL-based action recommendation
- POST /api/v1/predictions/explain       — XAI decision explainability

Compatible with Python 3.10.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.common.response import ApiResponse
from app.core.database.session import get_db
from app.core.middleware.rate_limiter import limiter
from app.core.security.jwt import RequireRole, get_current_active_user, get_optional_user
from app.modules.auth.models import User
from app.modules.prediction.schemas import (
    CasualtyForecastDTO,
    DisasterPredictionRequest,
    DisasterRiskForecastDTO,
    DisasterSpreadPredictionRequest,
    DisasterSpreadPredictionResponse,
    ExplainabilityRequest,
    ExplainabilityResponse,
    FireSpreadForecastDTO,
    FloodRiskForecastDTO,
    HospitalLoadForecastDTO,
    PredictionOutcomeRecordRequest,
    PredictionRecordResponse,
    PredictionResponse,
    PredictiveDashboardResponse,
    ResourceDemandForecastDTO,
    ResourceOptimizationRequest,
    ResourceOptimizationResponse,
    RLRecommendationRequest,
    RLRecommendationResponse,
)
from app.modules.prediction.service import PredictionService

router = APIRouter(prefix="/predictions", tags=["AI & Prediction Engine"])


# -------------------------------------------------------------------------
# Consolidated Predictive Dashboard
# -------------------------------------------------------------------------


@router.get(
    "/dashboard",
    response_model=ApiResponse[PredictiveDashboardResponse],
    summary="Get consolidated predictive dashboard",
    description="Returns multi-horizon (+5m, +15m, +30m, +60m) forecasts across disaster domains.",
)
def get_predictive_dashboard(
    simulation_id: str | None = Query(None, description="Optional simulation ID"),
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[PredictiveDashboardResponse]:
    result = PredictionService.get_predictive_dashboard(db, simulation_id=simulation_id)
    return ApiResponse.ok(
        data=result,
        message="Predictive dashboard telemetry generated.",
    )


@router.get(
    "/casualties",
    response_model=ApiResponse[CasualtyForecastDTO],
    summary="Get casualty and patient surge forecast",
)
def get_casualty_forecast(
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[CasualtyForecastDTO]:
    result = PredictionService.get_casualty_forecast(db)
    return ApiResponse.ok(data=result, message="Casualty forecast generated.")


@router.get(
    "/hospitals",
    response_model=ApiResponse[list[HospitalLoadForecastDTO]],
    summary="Get hospital capacity and ICU saturation forecast",
)
def get_hospital_forecast(
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[list[HospitalLoadForecastDTO]]:
    result = PredictionService.get_hospital_forecast(db)
    return ApiResponse.ok(data=result, message="Hospital load forecast generated.")


@router.get(
    "/resources",
    response_model=ApiResponse[list[ResourceDemandForecastDTO]],
    summary="Get emergency fleet demand and shortage forecast",
)
def get_resource_forecast(
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[list[ResourceDemandForecastDTO]]:
    result = PredictionService.get_resource_forecast(db)
    return ApiResponse.ok(data=result, message="Resource demand forecast generated.")


@router.get(
    "/disaster-risk",
    response_model=ApiResponse[list[DisasterRiskForecastDTO]],
    summary="Get spatial disaster risk and propagation forecast",
)
def get_disaster_risk_forecast(
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[list[DisasterRiskForecastDTO]]:
    result = PredictionService.get_risk_forecast(db)
    return ApiResponse.ok(data=result, message="Disaster risk forecast generated.")


@router.get(
    "/fire-spread",
    response_model=ApiResponse[list[FireSpreadForecastDTO]],
    summary="Get multi-horizon fire propagation zones",
)
def get_fire_spread_forecast(
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[list[FireSpreadForecastDTO]]:
    result = PredictionService.get_fire_spread_forecast(db)
    return ApiResponse.ok(data=result, message="Fire spread forecast generated.")


@router.get(
    "/flood-risk",
    response_model=ApiResponse[list[FloodRiskForecastDTO]],
    summary="Get flood inundation and road closure risk forecast",
)
def get_flood_risk_forecast(
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[list[FloodRiskForecastDTO]]:
    result = PredictionService.get_flood_risk_forecast(db)
    return ApiResponse.ok(data=result, message="Flood risk forecast generated.")


# -------------------------------------------------------------------------
# History and Outcome Verification
# -------------------------------------------------------------------------


@router.get(
    "/history",
    response_model=ApiResponse[dict],
    summary="List historical prediction records",
)
def list_prediction_history(
    prediction_type: str | None = Query(None),
    simulation_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User | None = Depends(get_optional_user),
) -> ApiResponse[dict]:
    skip = (page - 1) * page_size
    items, total = PredictionService.list_prediction_history(
        db, prediction_type=prediction_type, simulation_id=simulation_id, skip=skip, limit=page_size
    )
    return ApiResponse.paginated(
        data=[item.model_dump(mode="json") for item in items],
        total=total,
        page=page,
        page_size=page_size,
        message=f"Retrieved {len(items)} prediction record(s).",
    )


@router.post(
    "/history/{record_id}/outcome",
    response_model=ApiResponse[PredictionRecordResponse],
    summary="Record observed outcome for prediction error tracking",
)
def record_prediction_outcome(
    record_id: int,
    payload: PredictionOutcomeRecordRequest,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN", "COMMANDER"])),
) -> ApiResponse[PredictionRecordResponse]:
    result = PredictionService.record_outcome(db, record_id, payload)
    return ApiResponse.ok(data=result, message="Prediction outcome recorded.")


# -------------------------------------------------------------------------
# ML & Algorithm Endpoints (Maintained)
# -------------------------------------------------------------------------


@router.post(
    "/spread",
    response_model=ApiResponse[PredictionResponse],
    summary="Predict disaster spread radius using physics model + XAI",
)
@limiter.limit("20/minute")
async def predict_spread(
    request: Request,
    payload: DisasterPredictionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> ApiResponse[PredictionResponse]:
    result = await PredictionService.predict_spread(db, payload)
    return ApiResponse.ok(
        data=result,
        message="Disaster spread prediction generated.",
    )


@router.post(
    "/optimize",
    response_model=ApiResponse[ResourceOptimizationResponse],
    summary="AI-driven resource allocation optimization (COMMANDER+)",
)
@limiter.limit("20/minute")
def optimize_resources(
    request: Request,
    payload: ResourceOptimizationRequest,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN", "COMMANDER"])),
) -> ApiResponse[ResourceOptimizationResponse]:
    result = PredictionService.optimize_allocation(db, payload)
    return ApiResponse.ok(
        data=result,
        message="Resource allocation optimization complete.",
    )


@router.post(
    "/recommend",
    response_model=ApiResponse[RLRecommendationResponse],
    summary="RL-based next-best-action recommendation (COMMANDER+)",
)
@limiter.limit("20/minute")
def rl_recommend(
    request: Request,
    payload: RLRecommendationRequest,
    db: Session = Depends(get_db),
    _: User = Depends(RequireRole(["ADMIN", "COMMANDER", "DISPATCHER"])),
) -> ApiResponse[RLRecommendationResponse]:
    result = PredictionService.get_rl_recommendation(db, payload)
    return ApiResponse.ok(
        data=result,
        message="RL recommendation generated.",
    )


@router.post(
    "/explain",
    response_model=ApiResponse[ExplainabilityResponse],
    summary="XAI decision explainability — LLM narrative generation",
)
@limiter.limit("20/minute")
async def explain_decision(
    request: Request,
    payload: ExplainabilityRequest,
    _: User = Depends(get_current_active_user),
) -> ApiResponse[ExplainabilityResponse]:
    result = await PredictionService.explain_decision(payload)
    return ApiResponse.ok(
        data=result,
        message="Decision explanation generated.",
    )


@router.post(
    "/legacy/spread",
    response_model=ApiResponse[DisasterSpreadPredictionResponse],
    summary="[LEGACY] Disaster spread prediction",
    deprecated=True,
)
def legacy_predict_spread(
    payload: DisasterSpreadPredictionRequest,
    _: User = Depends(get_current_active_user),
) -> ApiResponse[DisasterSpreadPredictionResponse]:
    result = PredictionService.predict_disaster_spread(payload)
    return ApiResponse.ok(data=result, message="Legacy prediction computed.")
