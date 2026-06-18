from __future__ import annotations

from datetime import datetime, timezone

from app.analyzer import checks  # noqa: F401  (registers all checks)
from app.analyzer.context import AnalysisContext
from app.analyzer.parser import parse_manifest
from app.analyzer.registry import RULES, manifest_checks, resource_checks
from app.analyzer.resource import Manifest, Resource
from app.analyzer.scoring import build_scorecard
from app.analyzer.types import SEVERITY_ORDER
from app.schemas.analysis import (
    AnalysisMeta,
    AnalyzeRequest,
    AnalyzeResponse,
    CategoryCount,
    Finding,
    ResourceSummary,
    SeverityCounts,
)

SCHEMA_VERSION = "1.0"
CATEGORIES = ["Workload Security", "RBAC", "Network Exposure", "Secrets", "Reliability", "Hygiene"]


def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    manifest = parse_manifest(request.content)
    categories = _resolve_categories(request.options.categories)

    ctx = AnalysisContext(manifest, strict=request.options.strict, categories=categories)
    for resource in manifest.resources:
        for check in resource_checks():
            check(ctx, resource)
    for manifest_check_fn in manifest_checks():
        manifest_check_fn(ctx)

    findings = _sort_findings(ctx.findings)
    severity_counts = _severity_counts(findings)
    category_counts = _category_counts(findings)
    scorecard = build_scorecard(findings, severity_counts, len(RULES), len(ctx.fired_rules))
    resources = _resource_summaries(manifest, findings)

    return AnalyzeResponse(
        meta=AnalysisMeta(
            schema_version=SCHEMA_VERSION,
            name=request.name,
            project=request.project,
            environment=request.environment,
            strict=request.options.strict,
            generated_at=datetime.now(timezone.utc).isoformat(),
        ),
        scorecard=scorecard,
        summary=_summary(manifest, findings, scorecard.status),
        resource_count=len(manifest.resources),
        workload_count=len(manifest.workloads),
        namespace_count=len(manifest.namespaces),
        severity_counts=severity_counts,
        category_counts=category_counts,
        resources=resources,
        findings=findings,
        next_steps=_next_steps(findings),
        notes=_notes(manifest, findings),
    )


def _resolve_categories(requested: list[str] | None) -> set[str] | None:
    if not requested:
        return None
    return {category for category in requested if category in CATEGORIES}


def _sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(
        findings,
        key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.resource_kind, f.resource_name),
    )


def _severity_counts(findings: list[Finding]) -> SeverityCounts:
    counts = SeverityCounts()
    for finding in findings:
        setattr(counts, finding.severity, getattr(counts, finding.severity) + 1)
    return counts


def _category_counts(findings: list[Finding]) -> list[CategoryCount]:
    tally: dict[str, int] = {category: 0 for category in CATEGORIES}
    for finding in findings:
        tally[finding.category] = tally.get(finding.category, 0) + 1
    return [CategoryCount(category=category, count=tally[category]) for category in CATEGORIES if tally[category]]


def _container_images(resource: Resource) -> list[str]:
    images = []
    for container in resource.containers:
        image = container.get("image")
        if image:
            images.append(str(image))
    return images


def _resource_summaries(manifest: Manifest, findings: list[Finding]) -> list[ResourceSummary]:
    summaries: list[ResourceSummary] = []
    for resource in manifest.resources:
        related = [
            f
            for f in findings
            if f.resource_kind == resource.kind and f.resource_name == resource.name
        ]
        top = min((f.severity for f in related), key=lambda s: SEVERITY_ORDER[s], default=None)
        summaries.append(
            ResourceSummary(
                kind=resource.kind,
                name=resource.name,
                namespace=resource.namespace,
                containers=[c.get("name", "container") for c in resource.containers],
                images=_container_images(resource),
                finding_count=len(related),
                top_severity=top,
            )
        )
    return summaries


def _summary(manifest: Manifest, findings: list[Finding], status: str) -> str:
    resource_count = len(manifest.resources)
    if not findings:
        return f"Reviewed {resource_count} resource(s); no findings from the built-in rule set."
    blocking = sum(1 for f in findings if f.severity in {"critical", "high"})
    verb = {"fail": "is not ready to deploy", "review": "needs review before deploy", "pass": "looks deployable"}[status]
    return (
        f"Reviewed {resource_count} resource(s) and found {len(findings)} issue(s), "
        f"{blocking} of them high impact. This bundle {verb}."
    )


def _next_steps(findings: list[Finding]) -> list[str]:
    steps: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        if finding.severity in {"critical", "high"} and finding.rule_id not in seen:
            seen.add(finding.rule_id)
            steps.append(f"[{finding.severity.upper()}] {finding.resource_kind}/{finding.resource_name}: {finding.remediation}")
        if len(steps) >= 5:
            break
    if not steps:
        steps.append("No critical or high findings. Address medium and low items as part of normal hardening.")
    return steps


def _notes(manifest: Manifest, findings: list[Finding]) -> list[str]:
    notes: list[str] = []
    if not manifest.workloads:
        notes.append("No workload resource (Deployment, StatefulSet, Pod, ...) was found in this bundle.")
    notes.append("Podscope performs static review; pair it with admission control and runtime telemetry for production assurance.")
    return notes
