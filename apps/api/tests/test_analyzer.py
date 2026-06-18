import pytest

from app.analyzer import analyze
from app.analyzer.parser import ManifestParseError, parse_manifest
from app.schemas.analysis import AnalyzeOptions, AnalyzeRequest


def run(content: str, **options) -> object:
    request = AnalyzeRequest(name="test", content=content, options=AnalyzeOptions(**options))
    return analyze(request)


def rule_ids(result) -> set[str]:
    return {finding.rule_id for finding in result.findings}


def test_parses_multi_document_yaml():
    manifest = parse_manifest("kind: Pod\napiVersion: v1\nmetadata:\n  name: a\n---\nkind: Service\napiVersion: v1\nmetadata:\n  name: b")
    assert [r.kind for r in manifest.resources] == ["Pod", "Service"]


def test_empty_manifest_raises():
    with pytest.raises(ManifestParseError):
        parse_manifest("   ")


def test_non_resource_documents_are_ignored():
    with pytest.raises(ManifestParseError):
        parse_manifest("just: a map\nwithout: kind")


def test_privileged_pod_is_critical():
    result = run(
        """
apiVersion: v1
kind: Pod
metadata:
  name: demo
  namespace: app
spec:
  containers:
    - name: c
      image: nginx:1.27
      securityContext:
        privileged: true
"""
    )
    assert "PS-W001" in rule_ids(result)
    assert result.severity_counts.critical >= 1


def test_latest_tag_flagged():
    result = run(
        """
apiVersion: v1
kind: Pod
metadata:
  name: demo
  namespace: app
spec:
  containers:
    - name: c
      image: nginx:latest
"""
    )
    assert "PS-W013" in rule_ids(result)


def test_cluster_admin_binding_is_critical():
    result = run(
        """
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: b
roleRef:
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: sa
    namespace: ci
"""
    )
    assert "PS-A004" in rule_ids(result)


def test_hardcoded_secret_env_flagged():
    result = run(
        """
apiVersion: v1
kind: Pod
metadata:
  name: demo
  namespace: app
spec:
  containers:
    - name: c
      image: nginx:1.27
      env:
        - name: API_TOKEN
          value: "abcdef0123456789"
"""
    )
    assert "PS-S003" in rule_ids(result)


def test_allow_all_ingress_policy_flagged():
    result = run(
        """
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: p
  namespace: app
spec:
  podSelector: {}
  ingress:
    - {}
"""
    )
    assert "PS-N006" in rule_ids(result)


def test_scorecard_fields_present():
    result = run("apiVersion: v1\nkind: Pod\nmetadata:\n  name: a\n  namespace: app\nspec:\n  containers: []")
    card = result.scorecard
    assert 0 <= card.score <= 100
    assert card.grade in {"A", "B", "C", "D", "F"}
    assert card.checks_run == card.checks_passed + card.checks_failed


def test_clean_pod_has_no_critical():
    result = run(
        """
apiVersion: v1
kind: Pod
metadata:
  name: demo
  namespace: app
  labels:
    app.kubernetes.io/name: demo
    team: core
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: c
      image: nginx:1.27.3
      imagePullPolicy: IfNotPresent
      securityContext:
        runAsNonRoot: true
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
      resources:
        requests: {cpu: 100m, memory: 128Mi}
        limits: {cpu: 200m, memory: 256Mi}
      readinessProbe:
        httpGet: {path: /, port: 80}
      livenessProbe:
        httpGet: {path: /, port: 80}
"""
    )
    assert result.severity_counts.critical == 0
