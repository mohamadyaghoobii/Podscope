from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.schemas.analysis import ExampleManifest

_DIR = Path(__file__).parent

_CATALOG: tuple[tuple[str, str, str, str], ...] = (
    (
        "risky-web.yaml",
        "Risky web stack",
        "Privileged deployment, hostPath, LoadBalancer, plaintext ingress, and wildcard RBAC.",
        "risky",
    ),
    (
        "hardened-web.yaml",
        "Hardened web stack",
        "Non-root, pinned image, probes, limits, PDB, spread, and a scoped NetworkPolicy.",
        "hardened",
    ),
    (
        "risky-rbac.yaml",
        "Over-privileged RBAC",
        "cluster-admin binding, secrets access, pods/exec, and a system:authenticated subject.",
        "risky",
    ),
    (
        "public-ingress.yaml",
        "Public exposure",
        "Wildcard ingress host without TLS in front of a NodePort service.",
        "risky",
    ),
    (
        "privileged-daemonset.yaml",
        "Privileged node agent",
        "DaemonSet sharing all host namespaces with privileged containers and host root mount.",
        "risky",
    ),
    (
        "network-policy-example.yaml",
        "NetworkPolicy patterns",
        "Default-deny, an allow-all anti-pattern, and a correctly scoped policy side by side.",
        "reference",
    ),
)


@lru_cache
def load_examples() -> list[ExampleManifest]:
    examples: list[ExampleManifest] = []
    for filename, title, description, intent in _CATALOG:
        content = (_DIR / filename).read_text(encoding="utf-8").strip()
        examples.append(
            ExampleManifest(
                name=filename,
                title=title,
                description=description,
                intent=intent,  # type: ignore[arg-type]
                content=content,
            )
        )
    return examples


def get_example(name: str) -> ExampleManifest | None:
    return next((example for example in load_examples() if example.name == name), None)
