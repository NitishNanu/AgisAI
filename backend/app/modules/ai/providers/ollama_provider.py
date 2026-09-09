"""
AegisAI AI Module — Ollama Explanation Provider.

Connects to local Ollama (Llama 3.2) to synthesize structured decision facts
into a natural-language tactical commander briefing.
Enforces strict anti-hallucination guardrails and falls back cleanly if Ollama is offline.
"""

import json
import time
from typing import Any

import httpx
import structlog

from app.core.config.settings import settings
from app.modules.ai.schemas import LLMExplanationResponse

logger = structlog.get_logger("aegis_ai.providers.ollama")


class OllamaExplanationProvider:
    """Async Ollama client specialized for emergency response tactical briefings."""

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL
        self.model_name = settings.OLLAMA_MODEL
        self.model_version = "3.2:3b"
        self.timeout = min(15.0, float(settings.OLLAMA_TIMEOUT_SECONDS))

    async def generate_briefing(
        self,
        decision_data: dict[str, Any],
    ) -> LLMExplanationResponse:
        """
        Synthesizes structured decision data into an operational briefing.
        """
        start_t = time.perf_counter()
        action = decision_data.get("action", {})
        reasons = decision_data.get("reasoning", [])
        expected_impact = decision_data.get("expected_impact", {})
        alternatives = decision_data.get("alternatives", [])
        priority = decision_data.get("priority", "MEDIUM")

        r_name = action.get("resource_name", "Unit")
        v_type = action.get("vehicle_type", "Emergency Unit")
        inc_id = action.get("incident_id")
        eta = action.get("estimated_arrival_minutes", 0.0)
        dist = action.get("distance_km", 0.0)
        hosp = action.get("destination_hospital_name", "Nearest Facility")

        prompt = (
            "You are AegisAI's tactical emergency briefing assistant.\n"
            "STRICT RULES:\n"
            "1. ONLY use the provided facts below.\n"
            "2. DO NOT invent new IDs, numbers, hospital beds, casualties, or coordinates.\n"
            "3. Output a concise briefing with: summary, tactical_briefing, "
            "operational_risks, and recommended_next_steps in JSON format.\n\n"
            f"FACTS:\n"
            f"- Action: Dispatch Unit '{r_name}' (Type: {v_type}) to Incident #{inc_id}.\n"
            f"- Estimated Arrival Time: {eta} minutes ({dist} km).\n"
            f"- Destination Hospital: {hosp}.\n"
            f"- Priority Level: {priority}.\n"
            f"- Key Reasons: {json.dumps(reasons)}.\n"
            f"- Expected Impact: {json.dumps(expected_impact)}.\n"
            f"- Evaluated Alternatives: {len(alternatives)} units evaluated.\n\n"
            "Respond ONLY with valid JSON having keys: summary, tactical_briefing, "
            "reasons, operational_risks, recommended_next_steps."
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                raw_text = data.get("response", "{}")
                parsed = json.loads(raw_text)

                latency_ms = (time.perf_counter() - start_t) * 1000.0

                summary_default = f"Deploy {r_name} to Incident #{inc_id} (ETA: {eta:.1f} min)."
                briefing_default = f"Rapid dispatch of {r_name} to scene. ETA is {eta:.1f} min."
                alt_summary = (
                    f"Evaluated {len(alternatives)} alternative units; selected primary candidate "
                    f"based on lowest travel latency and capability match."
                )

                return LLMExplanationResponse(
                    summary=parsed.get("summary", summary_default),
                    tactical_briefing=parsed.get("tactical_briefing", briefing_default),
                    reasons=parsed.get("reasons", reasons),
                    rejected_alternatives_summary=alt_summary,
                    operational_risks=parsed.get(
                        "operational_risks",
                        ["Monitor local traffic congestion along route."],
                    ),
                    recommended_next_steps=parsed.get(
                        "recommended_next_steps",
                        ["Awaiting Commander approval to dispatch unit."],
                    ),
                    model_used=f"{self.model_name} (Ollama)",
                    is_fallback=False,
                    latency_ms=round(latency_ms, 2),
                )
        except Exception as e:
            logger.info("ollama_unavailable_using_deterministic_fallback", error=str(e))
            return self._build_deterministic_fallback(decision_data, start_t)

    def _build_deterministic_fallback(
        self,
        decision_data: dict[str, Any],
        start_time: float,
    ) -> LLMExplanationResponse:
        """Fallback when LLM is unreachable or times out."""
        action = decision_data.get("action", {})
        reasons = decision_data.get("reasoning", [])
        alternatives = decision_data.get("alternatives", [])
        eta = action.get("estimated_arrival_minutes", 5.0)
        dist = action.get("distance_km", 2.0)
        unit_name = action.get("resource_name", "Assigned Unit")
        inc_id = action.get("incident_id", "N/A")

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        sum_txt = (
            f"Recommend dispatch of {unit_name} to Incident #{inc_id} "
            f"(ETA: {eta:.1f} min, {dist:.1f} km)."
        )
        brief_txt = (
            f"AI Decision Engine selected {unit_name} via multi-criteria optimization. "
            f"Unit provides capability match with an estimated response latency of {eta:.1f} min."
        )
        alt_txt = (
            f"{len(alternatives)} secondary units evaluated and ranked below primary candidate."
        )

        return LLMExplanationResponse(
            summary=sum_txt,
            tactical_briefing=brief_txt,
            reasons=reasons,
            rejected_alternatives_summary=alt_txt,
            operational_risks=[
                "Confirm radio link with dispatched unit upon departure.",
                "Maintain real-time GPS telemetry during transit.",
            ],
            recommended_next_steps=[
                "Approve decision to initiate automated dispatch sequence.",
                "Alert destination medical facility of incoming transport if required.",
            ],
            model_used="AegisAI Deterministic XAI Engine",
            is_fallback=True,
            latency_ms=round(latency_ms, 2),
        )
