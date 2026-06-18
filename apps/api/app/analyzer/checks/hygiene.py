from __future__ import annotations

from app.analyzer.context import AnalysisContext
from app.analyzer.registry import register_rules, resource_check
from app.analyzer.resource import Resource
from app.analyzer.types import Rule

LABELS_DOC = "https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/"

_NAMESPACED = {
    "Pod",
    "Deployment",
    "StatefulSet",
    "DaemonSet",
    "Job",
    "CronJob",
    "ReplicaSet",
    "Service",
    "Ingress",
    "ConfigMap",
    "Secret",
    "Role",
    "RoleBinding",
    "ServiceAccount",
    "NetworkPolicy",
    "PodDisruptionBudget",
}

_NAME_LABELS = {"app.kubernetes.io/name", "app"}
_OWNER_LABELS = {"app.kubernetes.io/part-of", "team", "owner", "app.kubernetes.io/managed-by"}

register_rules(
    [
        Rule(
            id="PS-H001",
            title="Missing recommended app label",
            severity="low",
            category="Hygiene",
            description="A workload has no app.kubernetes.io/name or app label.",
            impact="Missing standard labels make selectors, dashboards, and cost reporting unreliable.",
            remediation="Add the recommended app.kubernetes.io labels to metadata and the pod template.",
            confidence="medium",
            references=(LABELS_DOC,),
        ),
        Rule(
            id="PS-H002",
            title="Namespaced resource without a namespace",
            severity="info",
            category="Hygiene",
            description="A namespaced resource does not set metadata.namespace.",
            impact="Relying on the active kubectl context for placement leads to resources landing in the wrong namespace.",
            remediation="Set metadata.namespace explicitly on every namespaced resource.",
            confidence="medium",
            references=(LABELS_DOC,),
        ),
        Rule(
            id="PS-H003",
            title="Workload in the default namespace",
            severity="low",
            category="Hygiene",
            description="A workload targets the default namespace.",
            impact="The default namespace mixes unrelated workloads and complicates quota, policy, and access control.",
            remediation="Deploy workloads into a dedicated, purpose-named namespace.",
            confidence="medium",
            references=(LABELS_DOC,),
        ),
        Rule(
            id="PS-H004",
            title="Missing ownership metadata",
            severity="info",
            category="Hygiene",
            description="A workload has no ownership label such as team, owner, or part-of.",
            impact="Without ownership metadata it is hard to route incidents and track accountability.",
            remediation="Add an owner or app.kubernetes.io/part-of label to identify the responsible team.",
            confidence="low",
            references=(LABELS_DOC,),
        ),
    ]
)


@resource_check
def check_hygiene(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind in _NAMESPACED and resource.namespace is None:
        ctx.report("PS-H002", resource, path="metadata.namespace")

    if not resource.is_workload:
        return

    labels = set(resource.labels)
    if resource.effective_namespace == "default":
        ctx.report("PS-H003", resource, path="metadata.namespace")
    if not labels & _NAME_LABELS:
        ctx.report("PS-H001", resource, path="metadata.labels")
    if not labels & _OWNER_LABELS:
        ctx.report("PS-H004", resource, path="metadata.labels")
