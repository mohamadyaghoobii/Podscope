from __future__ import annotations

from app.analyzer.types import CONFIDENCE_FACTOR, SEVERITY_WEIGHT
from app.schemas.analysis import Finding, Scorecard, SeverityCounts


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def build_scorecard(
    findings: list[Finding],
    severity_counts: SeverityCounts,
    checks_run: int,
    checks_failed: int,
) -> Scorecard:
    penalty = sum(
        SEVERITY_WEIGHT[finding.severity] * CONFIDENCE_FACTOR[finding.confidence]
        for finding in findings
    )
    score = max(0, min(100, round(100 - penalty)))
    grade = _grade(score)

    has_critical = severity_counts.critical > 0
    if has_critical or score < 60:
        status: str = "fail"
    elif score < 85:
        status = "review"
    else:
        status = "pass"

    explanation = _explanation(score, severity_counts, status)

    return Scorecard(
        score=score,
        grade=grade,
        status=status,  # type: ignore[arg-type]
        explanation=explanation,
        checks_run=checks_run,
        checks_passed=max(0, checks_run - checks_failed),
        checks_failed=checks_failed,
    )


def _explanation(score: int, counts: SeverityCounts, status: str) -> str:
    if not any([counts.critical, counts.high, counts.medium, counts.low]):
        return "No security or reliability issues were detected by the built-in rule set."

    drivers: list[str] = []
    for label, value in (
        ("critical", counts.critical),
        ("high", counts.high),
        ("medium", counts.medium),
        ("low", counts.low),
    ):
        if value:
            drivers.append(f"{value} {label}")

    summary = ", ".join(drivers)
    if status == "fail":
        return f"Score {score}/100. Blocking issues found ({summary}). Resolve critical and high findings before deploying."
    if status == "review":
        return f"Score {score}/100. Review recommended before deploy ({summary})."
    return f"Score {score}/100. Minor findings only ({summary})."
