from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

WORKLOAD_KINDS = {
    "Pod",
    "Deployment",
    "StatefulSet",
    "DaemonSet",
    "Job",
    "CronJob",
    "ReplicaSet",
    "ReplicationController",
}

CONTROLLER_KINDS = WORKLOAD_KINDS - {"Pod"}


@dataclass
class Resource:
    kind: str
    name: str
    namespace: str | None
    raw: dict[str, Any]
    index: int

    @property
    def metadata(self) -> dict[str, Any]:
        return self.raw.get("metadata") or {}

    @property
    def labels(self) -> dict[str, Any]:
        return self.metadata.get("labels") or {}

    @property
    def spec(self) -> dict[str, Any]:
        return self.raw.get("spec") or {}

    @property
    def is_workload(self) -> bool:
        return self.kind in WORKLOAD_KINDS

    @property
    def effective_namespace(self) -> str:
        return self.namespace or "default"

    @property
    def pod_spec(self) -> dict[str, Any]:
        spec = self.spec
        if self.kind == "Pod":
            return spec
        if self.kind == "CronJob":
            return (
                (((spec.get("jobTemplate") or {}).get("spec") or {}).get("template") or {}).get("spec")
                or {}
            )
        if self.kind in CONTROLLER_KINDS:
            return (spec.get("template") or {}).get("spec") or {}
        return {}

    @property
    def pod_security_context(self) -> dict[str, Any]:
        return self.pod_spec.get("securityContext") or {}

    @property
    def containers(self) -> list[dict[str, Any]]:
        pod_spec = self.pod_spec
        groups = (
            pod_spec.get("containers") or [],
            pod_spec.get("initContainers") or [],
            pod_spec.get("ephemeralContainers") or [],
        )
        return [item for group in groups for item in group if isinstance(item, dict)]

    def display_name(self) -> str:
        return f"{self.kind}/{self.name}"


@dataclass
class Manifest:
    resources: list[Resource] = field(default_factory=list)

    def of_kind(self, *kinds: str) -> list[Resource]:
        wanted = set(kinds)
        return [resource for resource in self.resources if resource.kind in wanted]

    @property
    def workloads(self) -> list[Resource]:
        return [resource for resource in self.resources if resource.is_workload]

    @property
    def namespaces(self) -> set[str]:
        found: set[str] = set()
        for resource in self.resources:
            if resource.kind == "Namespace":
                found.add(resource.name)
            elif resource.namespace:
                found.add(resource.namespace)
            elif resource.is_workload:
                found.add("default")
        return found
