from __future__ import annotations

from typing import Callable, Iterable

from app.analyzer.types import Rule

RULES: dict[str, Rule] = {}

ResourceCheck = Callable[["AnalysisContext", "Resource"], None]
ManifestCheck = Callable[["AnalysisContext"], None]

_RESOURCE_CHECKS: list[ResourceCheck] = []
_MANIFEST_CHECKS: list[ManifestCheck] = []


def register_rules(rules: Iterable[Rule]) -> None:
    for rule in rules:
        if rule.id in RULES:
            raise ValueError(f"Duplicate rule id: {rule.id}")
        RULES[rule.id] = rule


def resource_check(fn: ResourceCheck) -> ResourceCheck:
    _RESOURCE_CHECKS.append(fn)
    return fn


def manifest_check(fn: ManifestCheck) -> ManifestCheck:
    _MANIFEST_CHECKS.append(fn)
    return fn


def resource_checks() -> list[ResourceCheck]:
    return list(_RESOURCE_CHECKS)


def manifest_checks() -> list[ManifestCheck]:
    return list(_MANIFEST_CHECKS)
