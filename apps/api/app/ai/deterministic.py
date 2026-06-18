from __future__ import annotations

from app.schemas.ai import (
    AIRemediationRequest,
    AISummaryRequest,
    RemediationItem,
)
from app.schemas.analysis import AnalyzeResponse, Finding

_READINESS = {
    "pass": "Ready to deploy. Only low-impact polish remains.",
    "review": "Hold for review. Resolve the flagged issues, then re-run before deploying.",
    "fail": "Not ready to deploy. Blocking security or reliability issues are present.",
}


def headline(analysis: AnalyzeResponse) -> str:
    card = analysis.scorecard
    return f"Podscope score {card.score}/100 (grade {card.grade}) — {card.status.upper()}"


def executive_summary(analysis: AnalyzeResponse, audience: str) -> str:
    counts = analysis.severity_counts
    parts = [
        f"Podscope reviewed {analysis.resource_count} Kubernetes resource(s) across "
        f"{analysis.namespace_count} namespace(s) and scored the bundle {analysis.scorecard.score}/100 "
        f"(grade {analysis.scorecard.grade}).",
    ]
    if counts.critical or counts.high:
        parts.append(
            f"There are {counts.critical} critical and {counts.high} high findings that should be "
            "fixed before this reaches a cluster."
        )
    elif counts.medium or counts.low:
        parts.append("No critical or high findings; the remaining items are hardening and reliability improvements.")
    else:
        parts.append("No issues were detected by the built-in rule set.")

    top_categories = [c.category for c in sorted(analysis.category_counts, key=lambda c: c.count, reverse=True)[:3]]
    if top_categories:
        parts.append("The findings concentrate in " + ", ".join(top_categories) + ".")
    if audience == "developer":
        parts.append("Start with the prioritized fixes below; each one maps to a concrete YAML change.")
    return " ".join(parts)


def prioritized_fixes(analysis: AnalyzeResponse, limit: int = 6) -> list[str]:
    fixes: list[str] = []
    seen: set[str] = set()
    for finding in analysis.findings:
        if finding.severity in {"critical", "high", "medium"} and finding.rule_id not in seen:
            seen.add(finding.rule_id)
            fixes.append(
                f"{finding.severity.upper()} · {finding.resource_kind}/{finding.resource_name}: {finding.remediation}"
            )
        if len(fixes) >= limit:
            break
    return fixes


def remediation_items(analysis: AnalyzeResponse, request: AIRemediationRequest) -> list[RemediationItem]:
    findings = _select_findings(analysis, request)
    items: list[RemediationItem] = []
    for finding in findings:
        items.append(
            RemediationItem(
                rule_id=finding.rule_id,
                title=finding.title,
                severity=finding.severity,
                resource=f"{finding.resource_kind}/{finding.resource_name}",
                explanation=f"{finding.description} {finding.impact}",
                suggestion=finding.remediation,
                patch=finding.fixed_example,
            )
        )
    return items


def _select_findings(analysis: AnalyzeResponse, request: AIRemediationRequest) -> list[Finding]:
    if request.finding_id:
        return [f for f in analysis.findings if f.id == request.finding_id]
    if request.rule_id:
        return [f for f in analysis.findings if f.rule_id == request.rule_id]
    ranked = [f for f in analysis.findings if f.severity in {"critical", "high", "medium"}]
    return ranked[:8] or analysis.findings[:8]


def readiness(analysis: AnalyzeResponse) -> str:
    return _READINESS[analysis.scorecard.status]


def summary_audience(request: AISummaryRequest) -> str:
    return request.audience
