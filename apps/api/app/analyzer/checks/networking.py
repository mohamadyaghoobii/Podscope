from __future__ import annotations

from app.analyzer.context import AnalysisContext
from app.analyzer.registry import manifest_check, register_rules, resource_check
from app.analyzer.resource import Resource
from app.analyzer.types import Rule

INGRESS_TLS = "https://kubernetes.io/docs/concepts/services-networking/ingress/#tls"
NETWORK_POLICY = "https://kubernetes.io/docs/concepts/services-networking/network-policies/"

register_rules(
    [
        Rule(
            id="PS-N001",
            title="Service type LoadBalancer",
            severity="medium",
            category="Network Exposure",
            description="A Service of type LoadBalancer provisions a public endpoint.",
            impact="LoadBalancer services often expose workloads directly to the internet, bypassing ingress controls and WAFs.",
            remediation="Prefer ClusterIP behind a shared ingress or gateway, or use an internal load balancer annotation.",
            confidence="medium",
            references=(NETWORK_POLICY,),
        ),
        Rule(
            id="PS-N002",
            title="Service type NodePort",
            severity="medium",
            category="Network Exposure",
            description="A Service of type NodePort opens a port on every node.",
            impact="NodePort exposes the workload on all node IPs and is hard to firewall consistently.",
            remediation="Use ClusterIP behind an ingress controller instead of NodePort.",
            confidence="medium",
            references=(NETWORK_POLICY,),
        ),
        Rule(
            id="PS-N003",
            title="Ingress without TLS",
            severity="medium",
            category="Network Exposure",
            description="An Ingress does not define a TLS block.",
            impact="Traffic to the ingress can travel unencrypted, exposing credentials and session data.",
            remediation="Add spec.tls with a certificate secret, or manage certificates with cert-manager.",
            references=(INGRESS_TLS,),
        ),
        Rule(
            id="PS-N004",
            title="Ingress host is wildcard or empty",
            severity="medium",
            category="Network Exposure",
            description="An Ingress rule uses a wildcard host or no host at all.",
            impact="A wildcard or catch-all host can capture traffic for unintended domains.",
            remediation="Scope each ingress rule to an explicit fully-qualified host name.",
            confidence="medium",
            references=(INGRESS_TLS,),
        ),
        Rule(
            id="PS-N005",
            title="Namespace without NetworkPolicy",
            severity="medium",
            category="Network Exposure",
            description="A namespace has workloads but no NetworkPolicy in this bundle.",
            impact="Without a NetworkPolicy all pods can talk to each other, so a single compromise spreads laterally.",
            remediation="Apply a default-deny NetworkPolicy per namespace and allow only required flows.",
            confidence="medium",
            references=(NETWORK_POLICY,),
        ),
        Rule(
            id="PS-N006",
            title="NetworkPolicy allows all ingress",
            severity="high",
            category="Network Exposure",
            description="A NetworkPolicy permits ingress from every source.",
            impact="An allow-all ingress rule defeats the purpose of segmentation and exposes the pod to the whole cluster.",
            remediation="Restrict ingress to specific pod, namespace, or IP-block selectors.",
            references=(NETWORK_POLICY,),
        ),
        Rule(
            id="PS-N007",
            title="NetworkPolicy allows all egress",
            severity="medium",
            category="Network Exposure",
            description="A NetworkPolicy permits egress to every destination.",
            impact="Unrestricted egress lets a compromised pod exfiltrate data or reach command-and-control endpoints.",
            remediation="Restrict egress to required destinations and DNS only.",
            references=(NETWORK_POLICY,),
        ),
    ]
)


@resource_check
def check_service(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind != "Service":
        return
    service_type = resource.spec.get("type", "ClusterIP")
    if service_type == "LoadBalancer":
        ctx.report("PS-N001", resource, path="spec.type", evidence="type: LoadBalancer")
    elif service_type == "NodePort":
        ctx.report("PS-N002", resource, path="spec.type", evidence="type: NodePort")


@resource_check
def check_ingress(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind != "Ingress":
        return
    spec = resource.spec
    if not spec.get("tls"):
        ctx.report("PS-N003", resource, path="spec.tls", fixed_example="spec:\n  tls:\n    - hosts: [\"app.example.com\"]\n      secretName: app-tls")
    for rule in spec.get("rules") or []:
        if not isinstance(rule, dict):
            continue
        host = rule.get("host")
        if not host or "*" in str(host):
            ctx.report("PS-N004", resource, path="spec.rules[].host", evidence=f"host: {host or '(none)'}")


@resource_check
def check_network_policy(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind != "NetworkPolicy":
        return
    spec = resource.spec
    policy_types = spec.get("policyTypes") or []
    ingress = spec.get("ingress")
    egress = spec.get("egress")

    if _is_allow_all(ingress):
        ctx.report("PS-N006", resource, path="spec.ingress", evidence="ingress: [{}]")
    if _is_allow_all(egress):
        ctx.report("PS-N007", resource, path="spec.egress", evidence="egress: [{}]")
    del policy_types


def _is_allow_all(rules: object) -> bool:
    if not isinstance(rules, list):
        return False
    for rule in rules:
        if rule == {} or rule is None:
            return True
        if isinstance(rule, dict) and not rule.get("from") and not rule.get("to") and not rule.get("ports"):
            return True
    return False


@manifest_check
def check_namespace_coverage(ctx: AnalysisContext) -> None:
    policy_namespaces = {
        policy.effective_namespace for policy in ctx.manifest.of_kind("NetworkPolicy")
    }
    seen: set[str] = set()
    for workload in ctx.manifest.workloads:
        namespace = workload.effective_namespace
        if namespace in policy_namespaces or namespace in seen:
            continue
        seen.add(namespace)
        ctx.report(
            "PS-N005",
            workload,
            path="metadata.namespace",
            detail=f"Namespace '{namespace}' has workloads but no NetworkPolicy in this bundle.",
        )
