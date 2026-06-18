from __future__ import annotations

from app.analyzer.registry import RULES
from app.analyzer.resource import Manifest, Resource
from app.analyzer.types import SEVERITY_STATUS, Confidence, Severity
from app.schemas.analysis import Finding

_STRICT_ESCALATION: dict[Severity, Severity] = {
    "low": "medium",
    "medium": "high",
    "high": "critical",
}


class AnalysisContext:
    def __init__(
        self,
        manifest: Manifest,
        *,
        strict: bool = False,
        categories: set[str] | None = None,
    ) -> None:
        self.manifest = manifest
        self.strict = strict
        self.enabled_categories = categories
        self.findings: list[Finding] = []
        self.fired_rules: set[str] = set()

    def report(
        self,
        rule_id: str,
        resource: Resource,
        *,
        path: str | None = None,
        detail: str | None = None,
        evidence: str | None = None,
        fixed_example: str | None = None,
        severity: Severity | None = None,
        confidence: Confidence | None = None,
    ) -> None:
        rule = RULES[rule_id]
        if self.enabled_categories is not None and rule.category not in self.enabled_categories:
            return

        resolved_severity: Severity = severity or rule.severity
        if self.strict:
            resolved_severity = _STRICT_ESCALATION.get(resolved_severity, resolved_severity)

        self.fired_rules.add(rule_id)
        self.findings.append(
            Finding(
                id=f"{rule_id}-{len(self.findings) + 1}",
                rule_id=rule_id,
                title=rule.title,
                severity=resolved_severity,
                status=SEVERITY_STATUS[resolved_severity],
                category=rule.category,
                confidence=confidence or rule.confidence,
                resource_kind=resource.kind,
                resource_name=resource.name,
                namespace=resource.namespace,
                path=path,
                description=detail or rule.description,
                impact=rule.impact,
                remediation=rule.remediation,
                fixed_example=fixed_example,
                evidence=evidence,
                references=list(rule.references),
            )
        )
