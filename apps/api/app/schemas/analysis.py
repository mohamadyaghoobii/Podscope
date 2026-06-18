from pydantic import BaseModel, Field
from typing import Any, Literal

Severity = Literal["critical", "high", "medium", "low", "info"]


class AnalyzeRequest(BaseModel):
    name: str = Field(default="uploaded-manifest", max_length=120)
    content: str = Field(min_length=1)


class Finding(BaseModel):
    rule_id: str
    title: str
    severity: Severity
    target: str
    namespace: str | None = None
    resource_kind: str | None = None
    resource_name: str | None = None
    message: str
    remediation: str
    patch_hint: str | None = None
    references: list[str] = Field(default_factory=list)


class ResourceSummary(BaseModel):
    kind: str
    name: str
    namespace: str | None = None
    containers: list[str] = Field(default_factory=list)


class SeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class AnalyzeResponse(BaseModel):
    name: str
    score: int
    status: Literal["pass", "review", "fail"]
    resource_count: int
    workload_count: int
    namespace_count: int
    severity_counts: SeverityCounts
    resources: list[ResourceSummary]
    findings: list[Finding]
    notes: list[str] = Field(default_factory=list)


class RuleInfo(BaseModel):
    rule_id: str
    title: str
    default_severity: Severity
    category: str
    description: str


class ExampleManifest(BaseModel):
    name: str
    description: str
    content: str


class ErrorDetail(BaseModel):
    detail: str
    line: int | None = None
    column: int | None = None
    raw: Any | None = None
