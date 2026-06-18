from __future__ import annotations

K8S_SECURITY = "https://kubernetes.io/docs/concepts/security/"
POD_SECURITY_STANDARDS = "https://kubernetes.io/docs/concepts/security/pod-security-standards/"
NSA_HARDENING = "https://media.defense.gov/2022/Aug/29/2003066362/-1/-1/0/CTR_KUBERNETES_HARDENING_GUIDANCE_1.2_20220829.PDF"

DANGEROUS_CAPABILITIES = {
    "ALL",
    "SYS_ADMIN",
    "NET_ADMIN",
    "NET_RAW",
    "SYS_PTRACE",
    "SYS_MODULE",
    "SYS_RAWIO",
    "DAC_OVERRIDE",
    "DAC_READ_SEARCH",
    "SETUID",
    "SETGID",
    "MKNOD",
    "BPF",
    "PERFMON",
}

SENSITIVE_ENV_PATTERNS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "accesskey",
    "private_key",
    "credential",
    "passphrase",
)

PLACEHOLDER_VALUES = {
    "",
    "changeme",
    "change-me",
    "example",
    "placeholder",
    "redacted",
    "<redacted>",
    "xxx",
    "todo",
    "null",
    "none",
}


def image_tag(image: str) -> str | None:
    if not image:
        return None
    if "@sha256:" in image:
        return None
    last = image.rsplit("/", 1)[-1]
    if ":" not in last:
        return None
    return last.rsplit(":", 1)[-1]


def image_is_pinned(image: str) -> bool:
    if not image:
        return False
    if "@sha256:" in image:
        return True
    tag = image_tag(image)
    return bool(tag) and tag != "latest"


def looks_like_secret_value(value: object) -> bool:
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if candidate.lower() in PLACEHOLDER_VALUES:
        return False
    if "$(" in candidate or candidate.startswith("${"):
        return False
    return len(candidate) >= 8


def env_name_is_sensitive(name: str) -> bool:
    lowered = name.lower()
    return any(pattern in lowered for pattern in SENSITIVE_ENV_PATTERNS)
