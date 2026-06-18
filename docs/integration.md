# OpsDeck integration contract

Podscope is a standalone product, but its analysis output is designed to be ingested by the OpsDeck DevSecOps platform without any change to the engine. This document is the stable contract OpsDeck (or any other consumer) can rely on.

## Versioning

Every `POST /api/analyze` response carries `meta.schema_version`. The current version is **`1.0`**. Backwards-incompatible changes to the run or finding shape will bump this value; additive fields will not.

## Run schema

```jsonc
{
  "meta": {
    "schema_version": "1.0",
    "name": "checkout.yaml",
    "project": "storefront",        // optional, echoed from request
    "environment": "prod",          // optional, echoed from request
    "strict": false,
    "generated_at": "2026-06-18T12:00:00+00:00"  // ISO 8601 UTC
  },
  "scorecard": {
    "score": 10,                    // 0–100
    "grade": "F",                   // A | B | C | D | F
    "status": "fail",               // pass | review | fail
    "explanation": "…",
    "checks_run": 43,
    "checks_passed": 24,
    "checks_failed": 19
  },
  "summary": "…",
  "resource_count": 4,
  "workload_count": 1,
  "namespace_count": 1,
  "severity_counts": { "critical": 2, "high": 6, "medium": 9, "low": 7, "info": 2 },
  "category_counts": [ { "category": "Workload Security", "count": 14 } ],
  "resources": [ /* ResourceSummary[] */ ],
  "findings": [ /* Finding[] */ ],
  "next_steps": [ "…" ],
  "notes": [ "…" ]
}
```

## Finding schema

```jsonc
{
  "id": "PS-W001-1",                // unique within a run
  "rule_id": "PS-W001",             // stable rule identifier
  "title": "Privileged container",
  "severity": "critical",           // critical | high | medium | low | info
  "status": "fail",                 // fail | warn | pass | info
  "category": "Workload Security",  // one of six fixed categories
  "confidence": "high",             // high | medium | low
  "resource_kind": "Deployment",
  "resource_name": "storefront",
  "namespace": "prod",              // nullable
  "path": "spec.containers[web].securityContext.privileged",  // nullable
  "description": "…",
  "impact": "…",
  "remediation": "…",
  "fixed_example": "securityContext:\n  privileged: false",   // nullable
  "evidence": "privileged: true",   // nullable
  "references": ["https://…"]
}
```

The six categories are fixed: `Workload Security`, `RBAC`, `Network Exposure`, `Secrets`, `Reliability`, `Hygiene`. Rule identifiers are stable and prefixed by category (`PS-W` workload, `PS-A` RBAC, `PS-N` network, `PS-S` secrets, `PS-R` reliability, `PS-H` hygiene).

## Ingestion patterns

- **HTTP** — OpsDeck calls `POST /api/analyze` and stores the run verbatim. The whole payload is self-describing via `schema_version`.
- **Library** — OpsDeck imports `app.analyzer.analyze(request)` and consumes the same Pydantic models directly.
- **Mapping** — `finding.rule_id` + `finding.id` is a stable key for deduplication across runs; `scorecard.status` maps to a platform-level gate decision.

## Future connector ideas (not built here)

- A webhook that pushes each completed run to an OpsDeck ingestion endpoint.
- A CI mode that fails the pipeline when `scorecard.score` is below a configured threshold and emits the run as a build artifact.
- A GitHub Action that renders `next_steps` and `scorecard` as a pull-request "merge risk" comment.
