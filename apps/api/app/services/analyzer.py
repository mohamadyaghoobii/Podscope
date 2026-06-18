from __future__ import annotations

import yaml
from yaml.error import MarkedYAMLError, YAMLError
from app.schemas.analysis import AnalyzeResponse, ErrorDetail, Finding, ResourceSummary, SeverityCounts
from app.services.rules import RULE_MAP

WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob", "ReplicaSet", "ReplicationController", "Pod"}
DANGEROUS_CAPABILITIES = {"SYS_ADMIN", "NET_ADMIN", "SYS_PTRACE", "DAC_OVERRIDE", "SYS_MODULE", "SYS_RAWIO", "MKNOD"}


def parse_documents(content: str) -> list[dict]:
    try:
        docs = [doc for doc in yaml.safe_load_all(content) if doc]
    except MarkedYAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        raise ValueError(ErrorDetail(detail=str(exc), line=getattr(mark, "line", None), column=getattr(mark, "column", None)).model_dump()) from exc
    except YAMLError as exc:
        raise ValueError(ErrorDetail(detail=str(exc)).model_dump()) from exc

    clean_docs = []
    for doc in docs:
        if isinstance(doc, dict):
            clean_docs.append(doc)
    return clean_docs


def analyze_manifest(name: str, content: str) -> AnalyzeResponse:
    docs = parse_documents(content)
    findings: list[Finding] = []
    resources = [_resource_summary(doc) for doc in docs]
    namespaces = _namespaces(docs)
    workload_docs = [doc for doc in docs if doc.get("kind") in WORKLOAD_KINDS]

    for doc in docs:
        kind = doc.get("kind", "Unknown")
        if kind in WORKLOAD_KINDS:
            findings.extend(_check_workload(doc))
        if kind == "Service":
            findings.extend(_check_service(doc))
        if kind == "Ingress":
            findings.extend(_check_ingress(doc))
        if kind in {"Role", "ClusterRole"}:
            findings.extend(_check_rbac(doc))

    findings.extend(_check_network_policies(docs, workload_docs))
    severity_counts = _count_findings(findings)
    score = _score(severity_counts)
    status = "pass" if score >= 90 else "review" if score >= 65 else "fail"
    notes = _notes(docs, workload_docs, findings)

    return AnalyzeResponse(
        name=name,
        score=score,
        status=status,
        resource_count=len(docs),
        workload_count=len(workload_docs),
        namespace_count=len(namespaces),
        severity_counts=severity_counts,
        resources=resources,
        findings=findings,
        notes=notes,
    )


def _resource_summary(doc: dict) -> ResourceSummary:
    metadata = doc.get("metadata") or {}
    return ResourceSummary(
        kind=doc.get("kind", "Unknown"),
        name=metadata.get("name", "unnamed"),
        namespace=metadata.get("namespace"),
        containers=[container.get("name", "unnamed") for container in _containers(doc)],
    )


def _namespaces(docs: list[dict]) -> set[str]:
    namespaces = set()
    for doc in docs:
        metadata = doc.get("metadata") or {}
        if doc.get("kind") == "Namespace" and metadata.get("name"):
            namespaces.add(metadata["name"])
        elif metadata.get("namespace"):
            namespaces.add(metadata["namespace"])
        elif doc.get("kind") in WORKLOAD_KINDS:
            namespaces.add("default")
    return namespaces


def _pod_spec(doc: dict) -> dict:
    kind = doc.get("kind")
    spec = doc.get("spec") or {}
    if kind == "Pod":
        return spec
    if kind == "CronJob":
        return spec.get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {}) or {}
    if kind in {"Deployment", "StatefulSet", "DaemonSet", "Job", "ReplicaSet", "ReplicationController"}:
        return spec.get("template", {}).get("spec", {}) or {}
    return {}


def _containers(doc: dict) -> list[dict]:
    pod_spec = _pod_spec(doc)
    containers = pod_spec.get("containers") or []
    init_containers = pod_spec.get("initContainers") or []
    ephemeral = pod_spec.get("ephemeralContainers") or []
    return [item for item in [*containers, *init_containers, *ephemeral] if isinstance(item, dict)]


def _resource_target(doc: dict, container: dict | None = None) -> tuple[str, str | None, str, str]:
    kind = doc.get("kind", "Unknown")
    metadata = doc.get("metadata") or {}
    name = metadata.get("name", "unnamed")
    namespace = metadata.get("namespace") or "default"
    container_name = container.get("name") if container else None
    target = f"{kind}/{name}"
    if container_name:
        target = f"{target}:{container_name}"
    return target, namespace, kind, name


def _finding(rule_id: str, doc: dict, message: str, remediation: str, container: dict | None = None, patch_hint: str | None = None) -> Finding:
    rule = RULE_MAP[rule_id]
    target, namespace, kind, name = _resource_target(doc, container)
    return Finding(
        rule_id=rule_id,
        title=rule.title,
        severity=rule.default_severity,
        target=target,
        namespace=namespace,
        resource_kind=kind,
        resource_name=name,
        message=message,
        remediation=remediation,
        patch_hint=patch_hint,
        references=["https://kubernetes.io/docs/concepts/security/", "https://kubernetes.io/docs/concepts/workloads/pods/"],
    )


def _check_workload(doc: dict) -> list[Finding]:
    findings = []
    pod_spec = _pod_spec(doc)
    pod_security = pod_spec.get("securityContext") or {}

    if pod_spec.get("hostNetwork") or pod_spec.get("hostPID") or pod_spec.get("hostIPC"):
        findings.append(_finding(
            "KUBE-006",
            doc,
            "The workload uses one or more host namespaces.",
            "Avoid hostNetwork, hostPID, and hostIPC unless there is a strict operational requirement.",
            patch_hint="Set hostNetwork, hostPID, and hostIPC to false or remove them from the pod spec.",
        ))

    for volume in pod_spec.get("volumes") or []:
        if isinstance(volume, dict) and volume.get("hostPath"):
            findings.append(_finding(
                "KUBE-005",
                doc,
                f"Volume {volume.get('name', 'unnamed')} mounts a hostPath.",
                "Replace hostPath with a safer volume type or restrict it to read-only operational use.",
                patch_hint="Remove hostPath or replace it with emptyDir, configMap, secret, or a managed persistent volume.",
            ))

    pod_run_as_non_root = pod_security.get("runAsNonRoot")
    for container in _containers(doc):
        security = container.get("securityContext") or {}
        if security.get("privileged") is True:
            findings.append(_finding(
                "KUBE-001",
                doc,
                "The container runs in privileged mode.",
                "Disable privileged mode and grant only the minimal capability required.",
                container,
                "Set securityContext.privileged to false.",
            ))

        container_run_as_non_root = security.get("runAsNonRoot")
        if container_run_as_non_root is not True and pod_run_as_non_root is not True:
            findings.append(_finding(
                "KUBE-002",
                doc,
                "The container does not explicitly require a non-root user.",
                "Set runAsNonRoot to true and use a non-root image user.",
                container,
                "Set securityContext.runAsNonRoot to true and consider runAsUser with a non-zero UID.",
            ))

        if security.get("allowPrivilegeEscalation") is not False:
            findings.append(_finding(
                "KUBE-003",
                doc,
                "Privilege escalation is not explicitly disabled.",
                "Set allowPrivilegeEscalation to false for application containers.",
                container,
                "Set securityContext.allowPrivilegeEscalation to false.",
            ))

        added = set((security.get("capabilities") or {}).get("add") or [])
        risky = sorted(added.intersection(DANGEROUS_CAPABILITIES))
        if risky:
            findings.append(_finding(
                "KUBE-004",
                doc,
                f"The container adds risky Linux capabilities: {', '.join(risky)}.",
                "Remove dangerous capabilities and add only the minimal capability required.",
                container,
                "Drop all capabilities by default and only add specific low-risk capabilities when required.",
            ))

        resources = container.get("resources") or {}
        requests = resources.get("requests") or {}
        limits = resources.get("limits") or {}
        if not requests.get("cpu") or not requests.get("memory") or not limits.get("cpu") or not limits.get("memory"):
            findings.append(_finding(
                "KUBE-007",
                doc,
                "CPU or memory requests and limits are incomplete.",
                "Define CPU and memory requests and limits for predictable scheduling and safer cluster operations.",
                container,
                "Add resources.requests.cpu, resources.requests.memory, resources.limits.cpu, and resources.limits.memory.",
            ))

        image = container.get("image", "")
        if _image_is_mutable(image):
            findings.append(_finding(
                "KUBE-008",
                doc,
                f"Image {image or 'missing'} is mutable or not pinned.",
                "Use immutable image tags or digests and avoid latest tags in production.",
                container,
                "Pin image to a versioned tag or digest such as image@sha256:...",
            ))

        if not container.get("readinessProbe") or not container.get("livenessProbe"):
            findings.append(_finding(
                "KUBE-009",
                doc,
                "The container is missing a liveness or readiness probe.",
                "Add health probes so Kubernetes can route traffic safely and restart unhealthy containers.",
                container,
                "Add readinessProbe and livenessProbe that match the application health endpoint.",
            ))

    return findings


def _image_is_mutable(image: str) -> bool:
    if not image:
        return True
    if "@sha256:" in image:
        return False
    last_segment = image.rsplit("/", 1)[-1]
    if ":" not in last_segment:
        return True
    return last_segment.endswith(":latest")


def _check_service(doc: dict) -> list[Finding]:
    service_type = (doc.get("spec") or {}).get("type", "ClusterIP")
    if service_type in {"LoadBalancer", "NodePort"}:
        return [_finding(
            "KUBE-010",
            doc,
            f"Service type {service_type} exposes traffic beyond the cluster boundary.",
            "Prefer ClusterIP behind an Ingress or gateway unless direct exposure is required.",
            patch_hint="Review service.type and restrict exposure through an ingress controller or private load balancer.",
        )]
    return []


def _check_ingress(doc: dict) -> list[Finding]:
    spec = doc.get("spec") or {}
    if not spec.get("tls"):
        return [_finding(
            "KUBE-011",
            doc,
            "Ingress does not define TLS.",
            "Add TLS configuration and certificate management for public ingress traffic.",
            patch_hint="Add spec.tls with hosts and secretName, or use cert-manager annotations.",
        )]
    return []


def _check_rbac(doc: dict) -> list[Finding]:
    findings = []
    for rule in (doc.get("rules") or []):
        if "*" in (rule.get("verbs") or []) or "*" in (rule.get("resources") or []) or "*" in (rule.get("apiGroups") or []):
            findings.append(_finding(
                "KUBE-012",
                doc,
                "RBAC rule grants wildcard access.",
                "Replace wildcard permissions with explicit verbs, resources, and apiGroups.",
                patch_hint="Use least privilege Role or ClusterRole rules with explicit permissions.",
            ))
            break
    return findings


def _check_network_policies(docs: list[dict], workloads: list[dict]) -> list[Finding]:
    policy_namespaces = set()
    for doc in docs:
        if doc.get("kind") == "NetworkPolicy":
            metadata = doc.get("metadata") or {}
            policy_namespaces.add(metadata.get("namespace") or "default")

    findings = []
    seen = set()
    for workload in workloads:
        metadata = workload.get("metadata") or {}
        namespace = metadata.get("namespace") or "default"
        if namespace not in policy_namespaces and namespace not in seen:
            seen.add(namespace)
            findings.append(_finding(
                "KUBE-013",
                workload,
                f"Namespace {namespace} has workloads but no NetworkPolicy in this bundle.",
                "Add NetworkPolicy resources to restrict east-west traffic for sensitive workloads.",
                patch_hint="Start with a default-deny NetworkPolicy and allow required application flows explicitly.",
            ))
    return findings


def _count_findings(findings: list[Finding]) -> SeverityCounts:
    counts = SeverityCounts()
    for finding in findings:
        current = getattr(counts, finding.severity)
        setattr(counts, finding.severity, current + 1)
    return counts


def _score(counts: SeverityCounts) -> int:
    penalty = counts.critical * 18 + counts.high * 10 + counts.medium * 5 + counts.low * 2
    return max(0, min(100, 100 - penalty))


def _notes(docs: list[dict], workloads: list[dict], findings: list[Finding]) -> list[str]:
    notes = []
    if not docs:
        notes.append("No Kubernetes resources were parsed from the submitted content.")
    if docs and not workloads:
        notes.append("The bundle contains Kubernetes resources, but no workload resource was found.")
    if not findings and workloads:
        notes.append("No baseline findings were detected by the built-in rule set.")
    notes.append("Podscope performs static manifest review and should be paired with admission control and runtime telemetry for production assurance.")
    return notes
