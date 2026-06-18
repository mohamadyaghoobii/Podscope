from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.ai import (
    AIRemediationRequest,
    AIRemediationResponse,
    AISummaryRequest,
    AISummaryResponse,
)
from app.schemas.analysis import AnalyzeResponse


class AINotConfigured(RuntimeError):
    pass


class AIProvider(ABC):
    name: str = "base"
    enabled: bool = False

    @abstractmethod
    def summarize(self, request: AISummaryRequest, analysis: AnalyzeResponse) -> AISummaryResponse:
        ...

    @abstractmethod
    def remediate(self, request: AIRemediationRequest, analysis: AnalyzeResponse) -> AIRemediationResponse:
        ...
