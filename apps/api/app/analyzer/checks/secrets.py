from __future__ import annotations

from app.analyzer.checks.helpers import env_name_is_sensitive, looks_like_secret_value
from app.analyzer.context import AnalysisContext
from app.analyzer.registry import register_rules, resource_check
from app.analyzer.resource import Resource
from app.analyzer.types import Rule

SECRETS_DOC = "https://kubernetes.io/docs/concepts/configuration/secret/"

register_rules(
    [
        Rule(
            id="PS-S001",
            title="Secret stored in the manifest",
            severity="info",
            category="Secrets",
            description="A Secret object carries inline data in the manifest.",
            impact="Secrets in version-controlled manifests are only base64 encoded, not encrypted, and are easy to leak.",
            remediation="Manage Secret values with an external store (Sealed Secrets, External Secrets, Vault) and keep raw values out of Git.",
            confidence="medium",
            references=(SECRETS_DOC,),
        ),
        Rule(
            id="PS-S002",
            title="Secret-like value in ConfigMap",
            severity="medium",
            category="Secrets",
            description="A ConfigMap key looks like it holds a credential.",
            impact="ConfigMaps are plain text and readable by anyone with namespace access; credentials there are effectively public.",
            remediation="Move credential-like values into a Secret or an external secret manager.",
            confidence="medium",
            references=(SECRETS_DOC,),
        ),
        Rule(
            id="PS-S003",
            title="Hardcoded credential in env var",
            severity="high",
            category="Secrets",
            description="A container sets a credential-like environment variable to a literal value.",
            impact="Hardcoded credentials in the pod spec are visible to anyone who can read the manifest or the running pod.",
            remediation="Reference the value with valueFrom.secretKeyRef instead of an inline value.",
            confidence="medium",
            references=(SECRETS_DOC,),
        ),
        Rule(
            id="PS-S004",
            title="Secret consumed as an environment variable",
            severity="low",
            category="Secrets",
            description="A container injects a Secret value through an environment variable.",
            impact="Secret values exposed as env vars can leak through crash dumps, child processes, and logging.",
            remediation="Prefer mounting secrets as files via a projected volume where the workload allows it.",
            confidence="low",
            references=(SECRETS_DOC,),
        ),
    ]
)


@resource_check
def check_secret_object(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind != "Secret":
        return
    if resource.raw.get("data") or resource.raw.get("stringData"):
        ctx.report("PS-S001", resource, path="data", evidence=f"Secret '{resource.name}' carries inline data")


@resource_check
def check_configmap(ctx: AnalysisContext, resource: Resource) -> None:
    if resource.kind != "ConfigMap":
        return
    for key, value in (resource.raw.get("data") or {}).items():
        if env_name_is_sensitive(str(key)) and looks_like_secret_value(value):
            ctx.report(
                "PS-S002",
                resource,
                path=f"data.{key}",
                detail=f"ConfigMap key '{key}' looks like a credential.",
                evidence=f"{key}: <redacted>",
            )


@resource_check
def check_env_secrets(ctx: AnalysisContext, resource: Resource) -> None:
    if not resource.is_workload:
        return
    for container in resource.containers:
        name = container.get("name", "container")
        for env in container.get("env") or []:
            if not isinstance(env, dict):
                continue
            env_name = str(env.get("name", ""))
            value = env.get("value")
            value_from = env.get("valueFrom") or {}

            if env_name_is_sensitive(env_name) and looks_like_secret_value(value):
                ctx.report(
                    "PS-S003",
                    resource,
                    path=f"spec.containers[{name}].env.{env_name}",
                    detail=f"Environment variable '{env_name}' is set to a literal value.",
                    evidence=f"{env_name}: <redacted>",
                )
            elif value_from.get("secretKeyRef"):
                ctx.report(
                    "PS-S004",
                    resource,
                    path=f"spec.containers[{name}].env.{env_name}",
                    evidence=f"{env_name} <- secretKeyRef",
                )
