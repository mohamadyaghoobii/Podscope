from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low", "info"]
Confidence = Literal["high", "medium", "low"]
Status = Literal["fail", "warn", "pass", "info"]
RunStatus = Literal["pass", "review", "fail"]


class AnalyzeOptions(BaseModel):
    strict: bool = False
    categories: list[str] | None = None


class AnalyzeRequest(BaseModel):
    name: str = Field(default="manifest.yaml", max_length=160)
    content: str = Field(min_length=1)
    project: str | None = Field(default=None, max_length=160)
    environment: str | None = Field(default=None, max_length=60)
    options: AnalyzeOptions = Field(default_factory=AnalyzeOptions)


class Finding(BaseModel):
    id: str
    rule_id: str
    title: str
    severity: Severity
    status: Status
    category: str
    confidence: Confidence
    resource_kind: str
    resource_name: str
    namespace: str | None = None
    path: str | None = None
    description: str
    impact: str
    remediation: str
    fixed_example: str | None = None
    evidence: str | None = None
    references: list[str] = Field(default_factory=list)


class ResourceSummary(BaseModel):
    kind: str
    name: str
    namespace: str | None = None
    containers: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    finding_count: int = 0
    top_severity: Severity | None = None


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class CategoryCount(BaseModel):
    category: str
    count: int


class Scorecard(BaseModel):
    score: int
    grade: str
    status: RunStatus
    explanation: str
    checks_run: int
    checks_passed: int
    checks_failed: int


class AnalysisMeta(BaseModel):
    schema_version: str
    name: str
    project: str | None = None
    environment: str | None = None
    strict: bool = False
    generated_at: str


class AnalyzeResponse(BaseModel):
    meta: AnalysisMeta
    scorecard: Scorecard
    summary: str
    resource_count: int
    workload_count: int
    namespace_count: int
    severity_counts: SeverityCounts
    category_counts: list[CategoryCount]
    resources: list[ResourceSummary]
    findings: list[Finding]
    next_steps: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RuleInfo(BaseModel):
    id: str
    title: str
    severity: Severity
    category: str
    confidence: Confidence
    description: str
    impact: str
    remediation: str
    references: list[str] = Field(default_factory=list)


class ExampleManifest(BaseModel):
    name: str
    title: str
    description: str
    intent: Literal["risky", "hardened", "reference"]
    content: str


class ErrorDetail(BaseModel):
    detail: str
    line: int | None = None
    column: int | None = None
