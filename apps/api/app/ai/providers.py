from __future__ import annotations

from app.ai import deterministic
from app.ai.base import AINotConfigured, AIProvider
from app.schemas.ai import (
    AIRemediationRequest,
    AIRemediationResponse,
    AISummaryRequest,
    AISummaryResponse,
)
from app.schemas.analysis import AnalyzeResponse


class NullProvider(AIProvider):
    """Deterministic, dependency-free provider used when AI is disabled."""

    name = "none"
    enabled = False

    def summarize(self, request: AISummaryRequest, analysis: AnalyzeResponse) -> AISummaryResponse:
        return AISummaryResponse(
            provider=self.name,
            ai_enabled=False,
            headline=deterministic.headline(analysis),
            executive_summary=deterministic.executive_summary(analysis, request.audience),
            readiness=deterministic.readiness(analysis),
            prioritized_fixes=deterministic.prioritized_fixes(analysis),
        )

    def remediate(self, request: AIRemediationRequest, analysis: AnalyzeResponse) -> AIRemediationResponse:
        items = deterministic.remediation_items(analysis, request)
        return AIRemediationResponse(
            provider=self.name,
            ai_enabled=False,
            notes="Deterministic remediation generated from the rule engine. Set AI_PROVIDER to enable model-written explanations.",
            items=items,
        )


class LLMProvider(AIProvider):
    """Placeholder for hosted model providers (OpenAI, Anthropic, local).

    The deterministic analysis is always computed first and handed to the model
    as grounding context. Until an API key and client are wired in, this provider
    reports itself as unconfigured so callers can fall back gracefully.
    """

    def __init__(self, name: str, api_key: str | None, model: str | None) -> None:
        self.name = name
        self.model = model
        self._api_key = api_key
        self.enabled = bool(api_key)

    def _ensure_ready(self) -> None:
        if not self._api_key:
            raise AINotConfigured(
                f"AI provider '{self.name}' is selected but no API key is configured."
            )

    def summarize(self, request: AISummaryRequest, analysis: AnalyzeResponse) -> AISummaryResponse:
        self._ensure_ready()
        raise AINotConfigured(
            f"AI provider '{self.name}' is not implemented in this build. "
            "Wire in the client SDK to enable model-generated summaries."
        )

    def remediate(self, request: AIRemediationRequest, analysis: AnalyzeResponse) -> AIRemediationResponse:
        self._ensure_ready()
        raise AINotConfigured(
            f"AI provider '{self.name}' is not implemented in this build. "
            "Wire in the client SDK to enable model-generated remediation."
        )
