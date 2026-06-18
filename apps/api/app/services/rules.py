from app.schemas.analysis import RuleInfo


RULES = [
    RuleInfo(
        rule_id="KUBE-001",
        title="Privileged container",
        default_severity="critical",
        category="Workload security",
        description="Flags containers that run with securityContext.privileged set to true.",
    ),
    RuleInfo(
        rule_id="KUBE-002",
        title="Container may run as root",
        default_severity="high",
        category="Workload security",
        description="Flags workloads where runAsNonRoot is missing or explicitly disabled.",
    ),
    RuleInfo(
        rule_id="KUBE-003",
        title="Privilege escalation not blocked",
        default_severity="high",
        category="Workload security",
        description="Flags containers where allowPrivilegeEscalation is not set to false.",
    ),
    RuleInfo(
        rule_id="KUBE-004",
        title="Dangerous Linux capability added",
        default_severity="high",
        category="Workload security",
        description="Flags high-risk capabilities such as SYS_ADMIN, NET_ADMIN, SYS_PTRACE, or DAC_OVERRIDE.",
    ),
    RuleInfo(
        rule_id="KUBE-005",
        title="hostPath volume mounted",
        default_severity="high",
        category="Node exposure",
        description="Flags hostPath volumes that expose node filesystem paths to pods.",
    ),
    RuleInfo(
        rule_id="KUBE-006",
        title="Host namespace enabled",
        default_severity="high",
        category="Node exposure",
        description="Flags hostNetwork, hostPID, or hostIPC usage.",
    ),
    RuleInfo(
        rule_id="KUBE-007",
        title="Missing resource requests or limits",
        default_severity="medium",
        category="Reliability",
        description="Flags containers without CPU or memory requests and limits.",
    ),
    RuleInfo(
        rule_id="KUBE-008",
        title="Mutable or unpinned image tag",
        default_severity="medium",
        category="Supply chain",
        description="Flags images using latest or no explicit tag or digest.",
    ),
    RuleInfo(
        rule_id="KUBE-009",
        title="Missing liveness or readiness probe",
        default_severity="low",
        category="Reliability",
        description="Flags app containers without liveness or readiness probes.",
    ),
    RuleInfo(
        rule_id="KUBE-010",
        title="Service exposes workload broadly",
        default_severity="medium",
        category="Exposure",
        description="Flags NodePort and LoadBalancer services for manual review.",
    ),
    RuleInfo(
        rule_id="KUBE-011",
        title="Ingress missing TLS",
        default_severity="medium",
        category="Exposure",
        description="Flags Ingress resources without TLS configuration.",
    ),
    RuleInfo(
        rule_id="KUBE-012",
        title="RBAC wildcard permission",
        default_severity="high",
        category="Access control",
        description="Flags Role or ClusterRole rules that use wildcard verbs, resources, or apiGroups.",
    ),
    RuleInfo(
        rule_id="KUBE-013",
        title="Namespace has no NetworkPolicy",
        default_severity="medium",
        category="Network segmentation",
        description="Flags namespaces with workloads but no NetworkPolicy in the submitted bundle.",
    ),
]


RULE_MAP = {rule.rule_id: rule for rule in RULES}
