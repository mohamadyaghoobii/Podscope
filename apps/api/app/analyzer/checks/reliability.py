from __future__ import annotations

from app.analyzer.context import AnalysisContext
from app.analyzer.registry import register_rules, resource_check
from app.analyzer.resource import Resource
from app.analyzer.types import Rule

PROBES = "https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/"
RESOURCES_DOC = "https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/"
PDB_DOC = "https://kubernetes.io/docs/tasks/run-application/configure-pdb/"

_LONG_LIVED = {"Deployment", "StatefulSet", "ReplicaSet", "ReplicationController", "DaemonSet"}

register_rules(
    [
        Rule(
            id="PS-R001",
            title="Missing resource requests",
            severity="medium",
            category="Reliability",
            description="A container does not declare CPU and memory requests.",
            impact="Without requests the scheduler cannot place the pod safely, leading to noisy-neighbour contention and evictions.",
            remediation="Set resources.requests.cpu and resources.requests.memory based on observed usage.",
            references=(RESOURCES_DOC,),
        ),
        Rule(
            id="PS-R002",
            title="Missing resource limits",
            severity="medium",
            category="Reliability",
            description="A container does not declare CPU and/or memory limits.",
            impact="A container without limits can starve neighbours and trigger node-level OOM kills.",
            remediation="Set resources.limits.cpu and resources.limits.memory (memory limits are especially important).",
            references=(RESOURCES_DOC,),
        ),
        Rule(
            id="PS-R003",
            title="Missing liveness probe",
            severity="low",
            category="Reliability",
            description="A container has no livenessProbe.",
            impact="Kubernetes cannot detect and restart a hung container without a liveness probe.",
            remediation="Add a livenessProbe that checks a lightweight health endpoint.",
            references=(PROBES,),
        ),
        Rule(
            id="PS-R004",
            title="Missing readiness probe",
            severity="low",
            category="Reliability",
            description="A container has no readinessProbe.",
            impact="Traffic may be routed to a pod before it is ready, causing user-facing errors during rollouts.",
            remediation="Add a readinessProbe so the pod only receives traffic when it can serve it.",
            references=(PROBES,),
        ),
        Rule(
            id="PS-R005",
            title="Single replica for a long-lived workload",
            severity="low",
            category="Reliability",
            description="A Deployment or ReplicaSet runs a single replica.",
            impact="A single replica means any node drain, crash, or rollout causes a full outage.",
            remediation="Run at least two replicas and pair them with anti-affinity or topology spread.",
            confidence="medium",
            references=(PDB_DOC,),
        ),
        Rule(
            id="PS-R006",
            title="No PodDisruptionBudget for the workload",
            severity="info",
            category="Reliability",
            description="A multi-replica workload has no matching PodDisruptionBudget in this bundle.",
            impact="Voluntary disruptions such as node drains can take down all replicas at once.",
            remediation="Add a PodDisruptionBudget with minAvailable or maxUnavailable for the workload.",
            confidence="medium",
            references=(PDB_DOC,),
        ),
        Rule(
            id="PS-R007",
            title="No spread or anti-affinity",
            severity="info",
            category="Reliability",
            description="A multi-replica workload has no topologySpreadConstraints or pod anti-affinity.",
            impact="Replicas may co-locate on one node, removing the availability benefit of running multiple replicas.",
            remediation="Add topologySpreadConstraints or podAntiAffinity to spread replicas across nodes or zones.",
            confidence="low",
            references=(RESOURCES_DOC,),
        ),
    ]
)


@resource_check
def check_reliability(ctx: AnalysisContext, resource: Resource) -> None:
    if not resource.is_workload:
        return

    pod_spec = resource.pod_spec
    for container in pod_spec.get("containers") or []:
        if not isinstance(container, dict):
            continue
        name = container.get("name", "container")
        base = f"spec.containers[{name}]"
        resources = container.get("resources") or {}
        requests = resources.get("requests") or {}
        limits = resources.get("limits") or {}

        if not requests.get("cpu") or not requests.get("memory"):
            ctx.report("PS-R001", resource, path=f"{base}.resources.requests", fixed_example="resources:\n  requests:\n    cpu: 100m\n    memory: 128Mi")
        if not limits.get("cpu") or not limits.get("memory"):
            ctx.report("PS-R002", resource, path=f"{base}.resources.limits", fixed_example="resources:\n  limits:\n    cpu: 500m\n    memory: 256Mi")

        if not container.get("livenessProbe"):
            ctx.report("PS-R003", resource, path=f"{base}.livenessProbe")
        if not container.get("readinessProbe"):
            ctx.report("PS-R004", resource, path=f"{base}.readinessProbe")

    if resource.kind in {"Deployment", "ReplicaSet"}:
        replicas = resource.spec.get("replicas")
        if replicas is not None and replicas < 2:
            ctx.report("PS-R005", resource, path="spec.replicas", evidence=f"replicas: {replicas}")
        if (replicas or 0) >= 2:
            _check_disruption(ctx, resource, pod_spec)


def _check_disruption(ctx: AnalysisContext, resource: Resource, pod_spec: dict) -> None:
    has_pdb = any(
        pdb.spec.get("selector") for pdb in ctx.manifest.of_kind("PodDisruptionBudget")
    )
    if not has_pdb:
        ctx.report("PS-R006", resource, path="spec")

    affinity = (pod_spec.get("affinity") or {}).get("podAntiAffinity")
    spread = pod_spec.get("topologySpreadConstraints")
    if not affinity and not spread:
        ctx.report("PS-R007", resource, path="spec.template.spec")
