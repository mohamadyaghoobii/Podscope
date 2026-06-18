from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Severity = Literal["critical", "high", "medium", "low", "info"]
Confidence = Literal["high", "medium", "low"]
Status = Literal["fail", "warn", "pass", "info"]
Category = Literal[
    "Workload Security",
    "RBAC",
    "Network Exposure",
    "Secrets",
    "Reliability",
    "Hygiene",
]

SEVERITY_ORDER: dict[Severity, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

SEVERITY_WEIGHT: dict[Severity, int] = {
    "critical": 25,
    "high": 12,
    "medium": 6,
    "low": 2,
    "info": 0,
}

CONFIDENCE_FACTOR: dict[Confidence, float] = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.45,
}

SEVERITY_STATUS: dict[Severity, Status] = {
    "critical": "fail",
    "high": "fail",
    "medium": "warn",
    "low": "warn",
    "info": "info",
}


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    severity: Severity
    category: Category
    description: str
    impact: str
    remediation: str
    confidence: Confidence = "high"
    references: tuple[str, ...] = field(default_factory=tuple)
