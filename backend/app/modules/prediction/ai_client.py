"""
AegisAI Prediction Module — Ollama LLM Client.

Calls the local Ollama instance (Llama 3.2) to generate XAI explanations
for disaster spread predictions and action recommendations.
"""

import httpx
import structlog

from app.core.config.settings import settings

logger = structlog.get_logger("aegis_ai.prediction.ai_client")


class OllamaClient:
    """Async client for local Ollama LLM inference."""

    def __init__(self) -> None:
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT_SECONDS

    async def generate_explanation(
        self,
        incident_type: str,
        severity: str,
        radius: float,
        time_horizon: float,
        predicted_radius: float,
    ) -> str:
        """
        Generate an XAI explanation for a disaster spread prediction.
        Falls back to a deterministic template if Ollama is unreachable.
        """
        prompt = (
            f"You are an AI assistant for the AegisAI Disaster Management System. "
            f"A {severity} {incident_type} currently has an affected radius of {radius} meters. "
            f"Our predictive model estimates that in {time_horizon} hours, "
            f"the radius will expand to {predicted_radius} meters. "
            f"Briefly explain in 2-3 sentences what this means for emergency responders "
            f"and what actions they should prioritize."
        )

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    res_val = data.get("response") if isinstance(data, dict) else ""
                    return str(res_val or "").strip()
                logger.warning("ollama_non_200", status_code=response.status_code)
                return self._fallback_explanation(incident_type, severity, radius, predicted_radius)
        except Exception as exc:
            logger.info("ollama_unavailable_using_fallback", error=str(exc))
            return self._fallback_explanation(incident_type, severity, radius, predicted_radius)

    async def raw_generate(self, prompt: str) -> str:
        """Generate a completion for an arbitrary prompt with fallback."""
        return await self.generate(prompt)

    async def generate(self, prompt: str) -> str:
        """Generate a completion for an arbitrary prompt with fallback."""
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    res_val = data.get("response") if isinstance(data, dict) else ""
                    return str(res_val or "").strip()
                return "AI explanation unavailable (LLM service returned non-200)."
        except Exception as exc:
            logger.info("ollama_raw_generate_failed", error=str(exc))
            return (
                "AI decision explanation: The system evaluated proximity, team capabilities, "
                "and current incident severity to determine the optimal response action."
            )

    @staticmethod
    def _fallback_explanation(
        incident_type: str, severity: str, radius: float, predicted_radius: float
    ) -> str:
        growth = predicted_radius - radius
        return (
            f"The {severity.lower()} {incident_type.lower()} is projected to expand by "
            f"{growth:.0f}m to a total radius of {predicted_radius:.0f}m. "
            f"Emergency responders should establish a containment perimeter beyond the "
            f"predicted boundary and begin evacuation of the expanded zone immediately."
        )
