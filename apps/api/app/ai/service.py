from __future__ import annotations

from functools import lru_cache

from app.ai.base import AINotConfigured, AIProvider
from app.ai.providers import LLMProvider, NullProvider
from app.core.settings import get_settings
from app.schemas.ai import (
    AIRemediationRequest,
    AIRemediationResponse,
    AISummaryRequest,
    AISummaryResponse,
)
from app.schemas.analysis import AnalyzeResponse


@lru_cache
def get_provider() -> AIProvider:
    settings = get_settings()
    provider = settings.ai_provider.lower()
    if provider in {"openai", "anthropic", "local"}:
        return LLMProvider(name=provider, api_key=settings.ai_api_key, model=settings.ai_model)
    return NullProvider()


_FALLBACK = NullProvider()


def summarize(request: AISummaryRequest, analysis: AnalyzeResponse) -> AISummaryResponse:
    provider = get_provider()
    try:
        return provider.summarize(request, analysis)
    except AINotConfigured:
        return _FALLBACK.summarize(request, analysis)


def remediate(request: AIRemediationRequest, analysis: AnalyzeResponse) -> AIRemediationResponse:
    provider = get_provider()
    try:
        return provider.remediate(request, analysis)
    except AINotConfigured:
        return _FALLBACK.remediate(request, analysis)


def provider_status() -> dict[str, object]:
    provider = get_provider()
    return {"provider": provider.name, "enabled": provider.enabled}
