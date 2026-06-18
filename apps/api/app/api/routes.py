from fastapi import APIRouter, HTTPException
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse, ExampleManifest, RuleInfo
from app.services.analyzer import analyze_manifest
from app.services.rules import RULES

router = APIRouter(prefix="/api")


@router.get("/rules", response_model=list[RuleInfo])
def list_rules() -> list[RuleInfo]:
    return RULES


@router.get("/examples", response_model=list[ExampleManifest])
def examples() -> list[ExampleManifest]:
    return [
        ExampleManifest(
            name="risky-web.yaml",
            description="A deliberately risky deployment, service, ingress, and RBAC bundle.",
            content=RISKY_EXAMPLE,
        ),
        ExampleManifest(
            name="hardened-web.yaml",
            description="A safer baseline deployment with probes, limits, non-root execution, and network policy.",
            content=HARDENED_EXAMPLE,
        ),
    ]


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        return analyze_manifest(request.name, request.content)
    except ValueError as exc:
        raw = exc.args[0] if exc.args else {"detail": "Unable to parse manifest"}
        raise HTTPException(status_code=422, detail=raw) from exc


RISKY_EXAMPLE = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: storefront
  namespace: prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: storefront
  template:
    metadata:
      labels:
        app: storefront
    spec:
      hostNetwork: true
      volumes:
        - name: host-root
          hostPath:
            path: /
      containers:
        - name: web
          image: nginx:latest
          securityContext:
            privileged: true
            capabilities:
              add: ["SYS_ADMIN"]
          volumeMounts:
            - name: host-root
              mountPath: /host
---
apiVersion: v1
kind: Service
metadata:
  name: storefront
  namespace: prod
spec:
  type: LoadBalancer
  selector:
    app: storefront
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: storefront
  namespace: prod
spec:
  rules:
    - host: storefront.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: storefront
                port:
                  number: 80
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: broad-admin
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
""".strip()

HARDENED_EXAMPLE = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: storefront
  namespace: prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: storefront
  template:
    metadata:
      labels:
        app: storefront
    spec:
      securityContext:
        runAsNonRoot: true
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: web
          image: nginx:1.27.3
          ports:
            - containerPort: 8080
          securityContext:
            allowPrivilegeEscalation: false
            capabilities:
              drop: ["ALL"]
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /healthz
              port: 8080
          livenessProbe:
            httpGet:
              path: /livez
              port: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: storefront
  namespace: prod
spec:
  type: ClusterIP
  selector:
    app: storefront
  ports:
    - port: 80
      targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: storefront-default-deny
  namespace: prod
spec:
  podSelector:
    matchLabels:
      app: storefront
  policyTypes:
    - Ingress
    - Egress
""".strip()
