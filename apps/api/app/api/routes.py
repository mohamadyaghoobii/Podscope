from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.ai import remediate as ai_remediate
from app.ai import summarize as ai_summarize
from app.analyzer import ManifestParseError, analyze
from app.analyzer.registry import RULES
from app.examples import load_examples
from app.schemas.ai import (
    AIRemediationRequest,
    AIRemediationResponse,
    AISummaryRequest,
    AISummaryResponse,
)
from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
    ExampleManifest,
    RuleInfo,
)

router = APIRouter(prefix="/api")


@router.get("/rules", response_model=list[RuleInfo])
def list_rules() -> list[RuleInfo]:
    return [
        RuleInfo(
            id=rule.id,
            title=rule.title,
            severity=rule.severity,
            category=rule.category,
            confidence=rule.confidence,
            description=rule.description,
            impact=rule.impact,
            remediation=rule.remediation,
            references=list(rule.references),
        )
        for rule in RULES.values()
    ]


@router.get("/examples", response_model=list[ExampleManifest])
def list_examples() -> list[ExampleManifest]:
    return load_examples()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_manifest(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze(request)
    except ManifestParseError as exc:
        raise HTTPException(
            status_code=422,
            detail={"detail": exc.detail, "line": exc.line, "column": exc.column},
        ) from exc


@router.post("/ai/summarize", response_model=AISummaryResponse)
def ai_summarize_route(request: AISummaryRequest) -> AISummaryResponse:
    analysis = _safe_analyze(request)
    return ai_summarize(request, analysis)


@router.post("/ai/remediate", response_model=AIRemediationResponse)
def ai_remediate_route(request: AIRemediationRequest) -> AIRemediationResponse:
    analysis = _safe_analyze(request)
    return ai_remediate(request, analysis)


def _safe_analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze(request)
    except ManifestParseError as exc:
        raise HTTPException(
            status_code=422,
            detail={"detail": exc.detail, "line": exc.line, "column": exc.column},
        ) from exc
