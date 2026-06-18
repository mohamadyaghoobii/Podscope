from __future__ import annotations

from app.analyzer.context import AnalysisContext
from app.analyzer.registry import register_rules, resource_check
from app.analyzer.resource import Resource
from app.analyzer.types import Rule

RBAC_DOC = "https://kubernetes.io/docs/reference/access-authn-authz/rbac/"

_ROLE_KINDS = {"Role", "ClusterRole"}
_BINDING_KINDS = {"RoleBinding", "ClusterRoleBinding"}
_RISKY_SUBJECTS = {"system:anonymous", "system:unauthenticated", "system:authenticated"}
_WRITE_VERBS = {"create", "update", "patch", "delete", "deletecollection", "*"}

register_rules(
    [
        Rule(
            id="PS-A001",
            title="Wildcard verbs in RBAC rule",
            severity="high",
            category="RBAC",
            description="An RBAC rule grants the wildcard verb '*'.",
            impact="Wildcard verbs allow every action including delete and escalate on the matched resources.",
            remediation="List only the specific verbs the subject needs, such as get, list, and watch.",
            references=(RBAC_DOC,),
        ),
        Rule(
            id="PS-A002",
            title="Wildcard resources in RBAC rule",
            severity="high",
            category="RBAC",
            description="An RBAC rule grants access to the wildcard resource '*'.",
            impact="Wildcard resources expose secrets, pods/exec, and every other API object to the subject.",
            remediation="Enumerate the exact resources the subject needs.",
            references=(RBAC_DOC,),
        ),
        Rule(
            id="PS-A003",
            title="Wildcard API groups in RBAC rule",
            severity="medium",
            category="RBAC",
            description="An RBAC rule grants access across all API groups.",
            impact="A wildcard apiGroup broadens the rule to every installed CRD and core API.",
            remediation="Scope rules to specific API groups such as \"\" or apps.",
            confidence="medium",
            references=(RBAC_DOC,),
        ),
        Rule(
            id="PS-A004",
            title="Binding grants cluster-admin",
            severity="critical",
            category="RBAC",
            description="A binding references the built-in cluster-admin role.",
            impact="cluster-admin grants unrestricted control of the entire cluster to the bound subjects.",
            remediation="Bind a narrowly scoped Role or ClusterRole instead of cluster-admin.",
            references=(RBAC_DOC,),
        ),
        Rule(
            id="PS-A005",
            title="Binding exposes a broad subject",
            severity="critical",
            category="RBAC",
            description="A binding grants permissions to anonymous, unauthenticated, or all authenticated users.",
            impact="Binding privileges to system:anonymous or system:authenticated can hand control to any caller.",
            remediation="Bind specific ServiceAccounts or named users instead of broad system groups.",
            references=(RBAC_DOC,),
        ),
        Rule(
            id="PS-A006",
            title="Broad access to Secrets",
            severity="high",
            category="RBAC",
            description="An RBAC rule grants read or write access to Secrets.",
            impact="Read access to Secrets exposes credentials; write access enables privilege escalation.",
            remediation="Limit Secret access to named resources and the minimum verbs required.",
            confidence="medium",
            references=(RBAC_DOC,),
        ),
    ]
)


@resource_check
def check_role(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind not in _ROLE_KINDS:
        return
    for index, rule in enumerate(resource.raw.get("rules") or []):
        if not isinstance(rule, dict):
            continue
        path = f"rules[{index}]"
        verbs = {str(v).lower() for v in (rule.get("verbs") or [])}
        resources = {str(r).lower() for r in (rule.get("resources") or [])}
        api_groups = [str(g) for g in (rule.get("apiGroups") or [])]

        if "*" in verbs:
            ctx.report("PS-A001", resource, path=f"{path}.verbs", evidence="verbs: ['*']")
        if "*" in resources:
            ctx.report("PS-A002", resource, path=f"{path}.resources", evidence="resources: ['*']")
        if "*" in api_groups:
            ctx.report("PS-A003", resource, path=f"{path}.apiGroups", evidence="apiGroups: ['*']")
        if ("secrets" in resources or "*" in resources) and (verbs & _WRITE_VERBS or "get" in verbs or "list" in verbs or "watch" in verbs):
            ctx.report("PS-A006", resource, path=f"{path}.resources", evidence="resources include secrets")


@resource_check
def check_binding(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind not in _BINDING_KINDS:
        return
    role_ref = resource.raw.get("roleRef") or {}
    if role_ref.get("name") == "cluster-admin":
        ctx.report("PS-A004", resource, path="roleRef.name", evidence="roleRef.name: cluster-admin")

    for index, subject in enumerate(resource.raw.get("subjects") or []):
        if not isinstance(subject, dict):
            continue
        if subject.get("name") in _RISKY_SUBJECTS:
            ctx.report(
                "PS-A005",
                resource,
                path=f"subjects[{index}].name",
                detail=f"Binding grants access to '{subject.get('name')}'.",
                evidence=f"{subject.get('kind')}/{subject.get('name')}",
            )
