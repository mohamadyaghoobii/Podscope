from __future__ import annotations

import yaml
from yaml.error import MarkedYAMLError, YAMLError

from app.analyzer.resource import Manifest, Resource


class ManifestParseError(ValueError):
    def __init__(self, detail: str, line: int | None = None, column: int | None = None) -> None:
        super().__init__(detail)
        self.detail = detail
        self.line = line
        self.column = column


def parse_manifest(content: str) -> Manifest:
    if not content or not content.strip():
        raise ManifestParseError("The submitted manifest is empty.")

    try:
        documents = list(yaml.safe_load_all(content))
    except MarkedYAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        line = mark.line + 1 if mark is not None else None
        column = mark.column + 1 if mark is not None else None
        raise ManifestParseError(_clean_message(exc), line=line, column=column) from exc
    except YAMLError as exc:
        raise ManifestParseError(_clean_message(exc)) from exc

    resources: list[Resource] = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            continue
        kind = document.get("kind")
        if not isinstance(kind, str) or not kind:
            continue
        metadata = document.get("metadata") or {}
        name = metadata.get("name") if isinstance(metadata, dict) else None
        namespace = metadata.get("namespace") if isinstance(metadata, dict) else None
        resources.append(
            Resource(
                kind=kind,
                name=name or "unnamed",
                namespace=namespace,
                raw=document,
                index=index,
            )
        )

    if not resources:
        raise ManifestParseError(
            "No Kubernetes resources were found. Each document needs an apiVersion and kind."
        )

    return Manifest(resources=resources)


def _clean_message(exc: Exception) -> str:
    message = str(exc).strip()
    return message.splitlines()[0] if message else "The manifest could not be parsed as YAML."
