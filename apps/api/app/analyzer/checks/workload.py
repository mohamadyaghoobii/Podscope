from __future__ import annotations

from app.analyzer.checks.helpers import (
    DANGEROUS_CAPABILITIES,
    K8S_SECURITY,
    NSA_HARDENING,
    POD_SECURITY_STANDARDS,
    image_tag,
)
from app.analyzer.context import AnalysisContext
from app.analyzer.registry import register_rules, resource_check
from app.analyzer.resource import Resource
from app.analyzer.types import Rule

register_rules(
    [
        Rule(
            id="PS-W001",
            title="Privileged container",
            severity="critical",
            category="Workload Security",
            description="A container runs with securityContext.privileged set to true.",
            impact="Privileged containers can access all host devices and effectively escape the pod sandbox, giving an attacker full node control.",
            remediation="Remove privileged mode and grant only the specific Linux capabilities the workload needs.",
            references=(POD_SECURITY_STANDARDS, NSA_HARDENING),
        ),
        Rule(
            id="PS-W002",
            title="Container can run as root",
            severity="high",
            category="Workload Security",
            description="runAsNonRoot is not enforced at the pod or container level.",
            impact="Running as UID 0 widens the blast radius of a container compromise and bypasses many file-permission controls.",
            remediation="Set securityContext.runAsNonRoot to true and run the image as a dedicated non-zero UID.",
            references=(POD_SECURITY_STANDARDS,),
        ),
        Rule(
            id="PS-W003",
            title="Privilege escalation not disabled",
            severity="high",
            category="Workload Security",
            description="allowPrivilegeEscalation is not explicitly set to false.",
            impact="Processes can gain more privileges than their parent through setuid binaries or file capabilities.",
            remediation="Set securityContext.allowPrivilegeEscalation to false on every container.",
            references=(POD_SECURITY_STANDARDS,),
        ),
        Rule(
            id="PS-W004",
            title="Dangerous Linux capability added",
            severity="high",
            category="Workload Security",
            description="A container requests a high-risk Linux capability.",
            impact="Capabilities such as SYS_ADMIN or NET_ADMIN grant near-root powers and are common privilege-escalation paths.",
            remediation="Drop ALL capabilities and add back only the minimal, low-risk capabilities the workload genuinely needs.",
            references=(POD_SECURITY_STANDARDS, NSA_HARDENING),
        ),
        Rule(
            id="PS-W005",
            title="Capabilities not dropped",
            severity="medium",
            category="Workload Security",
            description="The container does not drop the default Linux capability set.",
            impact="Default capabilities expand the kernel attack surface available to a compromised process.",
            remediation="Add capabilities.drop: [\"ALL\"] and only add specific capabilities when required.",
            confidence="medium",
            references=(POD_SECURITY_STANDARDS,),
        ),
        Rule(
            id="PS-W006",
            title="hostPath volume mounted",
            severity="high",
            category="Workload Security",
            description="A volume mounts a path from the host filesystem.",
            impact="hostPath mounts let a pod read or modify node files and are a frequent container-escape vector.",
            remediation="Replace hostPath with emptyDir, configMap, secret, or a managed PersistentVolume; restrict to read-only if unavoidable.",
            references=(NSA_HARDENING,),
        ),
        Rule(
            id="PS-W007",
            title="Host network namespace shared",
            severity="high",
            category="Workload Security",
            description="hostNetwork is enabled on the pod.",
            impact="The pod shares the node network stack, bypassing NetworkPolicy and exposing host-local services.",
            remediation="Set hostNetwork to false unless a node-level agent strictly requires it.",
            references=(NSA_HARDENING,),
        ),
        Rule(
            id="PS-W008",
            title="Host PID namespace shared",
            severity="high",
            category="Workload Security",
            description="hostPID is enabled on the pod.",
            impact="The pod can see and signal all processes on the node, enabling reconnaissance and tampering.",
            remediation="Set hostPID to false.",
            references=(NSA_HARDENING,),
        ),
        Rule(
            id="PS-W009",
            title="Host IPC namespace shared",
            severity="high",
            category="Workload Security",
            description="hostIPC is enabled on the pod.",
            impact="The pod shares host inter-process communication, allowing access to other processes' shared memory.",
            remediation="Set hostIPC to false.",
            references=(NSA_HARDENING,),
        ),
        Rule(
            id="PS-W010",
            title="Missing seccomp profile",
            severity="medium",
            category="Workload Security",
            description="No seccompProfile is configured at the pod or container level.",
            impact="Without seccomp the container can call the full set of host syscalls, widening the kernel attack surface.",
            remediation="Set securityContext.seccompProfile.type to RuntimeDefault.",
            references=(POD_SECURITY_STANDARDS,),
        ),
        Rule(
            id="PS-W011",
            title="Writable root filesystem",
            severity="medium",
            category="Workload Security",
            description="readOnlyRootFilesystem is not enabled.",
            impact="A writable root filesystem lets an attacker drop tooling or persist changes inside the container.",
            remediation="Set securityContext.readOnlyRootFilesystem to true and mount emptyDir for paths that need writes.",
            references=(POD_SECURITY_STANDARDS,),
        ),
        Rule(
            id="PS-W012",
            title="Missing container securityContext",
            severity="medium",
            category="Workload Security",
            description="The container defines no securityContext at all.",
            impact="Containers without an explicit securityContext inherit permissive defaults.",
            remediation="Add a securityContext that disables privilege escalation, drops capabilities, and enforces a non-root user.",
            references=(POD_SECURITY_STANDARDS,),
        ),
        Rule(
            id="PS-W013",
            title="Image uses the latest tag",
            severity="medium",
            category="Workload Security",
            description="A container image uses the mutable latest tag.",
            impact="latest is mutable, so deployments are not reproducible and a compromised upstream tag is pulled silently.",
            remediation="Pin images to an immutable version tag or a digest such as image@sha256:...",
            references=(K8S_SECURITY,),
        ),
        Rule(
            id="PS-W014",
            title="Image is not pinned to a tag",
            severity="medium",
            category="Workload Security",
            description="A container image has no tag or digest.",
            impact="An untagged image resolves to latest at pull time, producing non-reproducible deployments.",
            remediation="Add an explicit version tag or digest to every image reference.",
            references=(K8S_SECURITY,),
        ),
        Rule(
            id="PS-W015",
            title="imagePullPolicy not explicit",
            severity="low",
            category="Workload Security",
            description="imagePullPolicy is not set while using a fixed tag.",
            impact="Implicit pull behaviour can serve a stale cached layer or re-pull unexpectedly across nodes.",
            remediation="Set imagePullPolicy to IfNotPresent for pinned tags or Always for tags that may move.",
            confidence="low",
            references=(K8S_SECURITY,),
        ),
    ]
)

_SECURITY_CONTEXT_FIX = """securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop: ["ALL"]"""


@resource_check
def check_workload(ctx: AnalysisContext, resource: Resource) -> None:
    if not resource.is_workload:
        return

    pod_spec = resource.pod_spec
    pod_sc = resource.pod_security_context

    if pod_spec.get("hostNetwork") is True:
        ctx.report("PS-W007", resource, path="spec.hostNetwork", evidence="hostNetwork: true")
    if pod_spec.get("hostPID") is True:
        ctx.report("PS-W008", resource, path="spec.hostPID", evidence="hostPID: true")
    if pod_spec.get("hostIPC") is True:
        ctx.report("PS-W009", resource, path="spec.hostIPC", evidence="hostIPC: true")

    for volume in pod_spec.get("volumes") or []:
        if isinstance(volume, dict) and volume.get("hostPath"):
            name = volume.get("name", "unnamed")
            path = (volume.get("hostPath") or {}).get("path", "?")
            ctx.report(
                "PS-W006",
                resource,
                path=f"spec.volumes[{name}].hostPath",
                evidence=f"hostPath.path: {path}",
            )

    pod_seccomp = (pod_sc.get("seccompProfile") or {}).get("type")
    pod_run_as_non_root = pod_sc.get("runAsNonRoot")

    for container in resource.containers:
        name = container.get("name", "container")
        base = f"spec.containers[{name}]"
        sc = container.get("securityContext") or {}

        if not sc:
            ctx.report("PS-W012", resource, path=f"{base}.securityContext", evidence="securityContext not set", fixed_example=_SECURITY_CONTEXT_FIX)

        if sc.get("privileged") is True:
            ctx.report("PS-W001", resource, path=f"{base}.securityContext.privileged", evidence="privileged: true", fixed_example="securityContext:\n  privileged: false")

        if sc.get("runAsNonRoot") is not True and pod_run_as_non_root is not True:
            ctx.report("PS-W002", resource, path=f"{base}.securityContext.runAsNonRoot", fixed_example="securityContext:\n  runAsNonRoot: true\n  runAsUser: 10001")

        if sc.get("allowPrivilegeEscalation") is not False:
            ctx.report("PS-W003", resource, path=f"{base}.securityContext.allowPrivilegeEscalation", fixed_example="securityContext:\n  allowPrivilegeEscalation: false")

        capabilities = sc.get("capabilities") or {}
        added = {str(item).upper() for item in (capabilities.get("add") or [])}
        risky = sorted(added & DANGEROUS_CAPABILITIES)
        if risky:
            ctx.report(
                "PS-W004",
                resource,
                path=f"{base}.securityContext.capabilities.add",
                detail=f"Container '{name}' adds high-risk capabilities: {', '.join(risky)}.",
                evidence=f"add: {risky}",
            )

        dropped = {str(item).upper() for item in (capabilities.get("drop") or [])}
        if "ALL" not in dropped:
            ctx.report("PS-W005", resource, path=f"{base}.securityContext.capabilities.drop", fixed_example="securityContext:\n  capabilities:\n    drop: [\"ALL\"]")

        container_seccomp = (sc.get("seccompProfile") or {}).get("type")
        if not pod_seccomp and not container_seccomp:
            ctx.report("PS-W010", resource, path=f"{base}.securityContext.seccompProfile", fixed_example="securityContext:\n  seccompProfile:\n    type: RuntimeDefault")

        if sc.get("readOnlyRootFilesystem") is not True:
            ctx.report("PS-W011", resource, path=f"{base}.securityContext.readOnlyRootFilesystem", fixed_example="securityContext:\n  readOnlyRootFilesystem: true")

        image = container.get("image", "")
        tag = image_tag(image)
        if not image:
            ctx.report("PS-W014", resource, path=f"{base}.image", evidence="image not set")
        elif "@sha256:" not in image and tag is None:
            ctx.report("PS-W014", resource, path=f"{base}.image", detail=f"Image '{image}' has no tag or digest.", evidence=image)
        elif tag == "latest":
            ctx.report("PS-W013", resource, path=f"{base}.image", detail=f"Image '{image}' uses the latest tag.", evidence=image)

        if image and "imagePullPolicy" not in container and (tag and tag != "latest"):
            ctx.report("PS-W015", resource, path=f"{base}.imagePullPolicy")
