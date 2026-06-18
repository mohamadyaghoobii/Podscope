from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.analysis import AnalyzeRequest


class AISummaryRequest(AnalyzeRequest):
    audience: str = Field(default="platform", max_length=40)


class AISummaryResponse(BaseModel):
    provider: str
    ai_enabled: bool
    headline: str
    executive_summary: str
    readiness: str
    prioritized_fixes: list[str] = Field(default_factory=list)


class AIRemediationRequest(AnalyzeRequest):
    finding_id: str | None = None
    rule_id: str | None = None


class RemediationItem(BaseModel):
    rule_id: str
    title: str
    severity: str
    resource: str
    explanation: str
    suggestion: str
    patch: str | None = None


class AIRemediationResponse(BaseModel):
    provider: str
    ai_enabled: bool
    notes: str
    items: list[RemediationItem] = Field(default_factory=list)
