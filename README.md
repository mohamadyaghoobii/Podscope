# Podscope

Podscope is a lightweight Kubernetes manifest review workspace for platform, SRE, and DevSecOps teams. It inspects Kubernetes YAML before it reaches a cluster and turns risky workload patterns into clear findings with remediation guidance.

![Podscope dashboard](docs/images/podscope-dashboard.svg)

## Why Podscope exists

Kubernetes reviews often happen too late: after manifests are merged, deployed, or already running in shared clusters. Podscope gives teams a fast static review loop for pull requests, design reviews, and pre-deployment checks.

It is not a replacement for admission control, runtime security, policy engines, or a full Kubernetes posture platform. It is a practical starter for reviewing manifests, teaching safer defaults, and connecting future modules into the larger OpsDeck ecosystem.

## What it checks today

Podscope currently reviews multi-document Kubernetes YAML for baseline security and reliability issues:

| Area | Examples |
| --- | --- |
| Workload hardening | privileged containers, root execution, privilege escalation, risky Linux capabilities |
| Node exposure | hostPath, hostNetwork, hostPID, hostIPC |
| Reliability | missing CPU or memory requests and limits, missing readiness or liveness probes |
| Supply chain | latest tags, missing tags, unpinned images |
| Exposure | LoadBalancer, NodePort, Ingress without TLS |
| Access control | wildcard RBAC permissions |
| Network segmentation | namespaces with workloads but no NetworkPolicy in the submitted bundle |

## Architecture

```text
podscope
├── apps
│   ├── api       FastAPI manifest analysis service
│   └── web       Next.js review interface
├── docs/images   Local README visuals
├── examples      Sample Kubernetes manifests
├── docker-compose.yml
└── README.md
```

## Tech stack

- FastAPI
- Pydantic
- PyYAML
- Next.js
- React
- TypeScript
- Docker Compose

## Local development with Docker Compose

```bash
docker compose up --build
```

Services:

| Service | URL |
| --- | --- |
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

## Manual backend setup

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On Windows PowerShell:

```powershell
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Manual frontend setup

```bash
cd apps/web
npm install
npm run dev
```

The frontend reads the API base URL from:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Environment variables

| Variable | Default | Description |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` | API endpoint used by the Next.js frontend |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Allowed browser origins for the API |

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| GET | `/ready` | Readiness check |
| GET | `/api/rules` | List built-in checks |
| GET | `/api/examples` | Return sample manifests |
| POST | `/api/analyze` | Analyze submitted Kubernetes YAML |

Example request:

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"name":"risky-web.yaml","content":"apiVersion: v1\nkind: Pod\nmetadata:\n  name: demo\nspec:\n  containers:\n    - name: web\n      image: nginx:latest"}'
```

## Response model

The analysis endpoint returns:

- Overall score
- Pass, review, or fail status
- Resource count
- Workload count
- Namespace count
- Severity counts
- Parsed resource summaries
- Findings with severity, message, remediation, and patch hint
- Review notes

## Testing

Backend tests:

```bash
cd apps/api
pip install -r requirements.txt
pytest
```

Syntax check:

```bash
cd apps/api
python -m py_compile app/main.py app/api/routes.py app/services/analyzer.py
```

Frontend build:

```bash
cd apps/web
npm install
npm run build
```

Docker Compose validation:

```bash
docker compose config
```

## Example manifests

Sample manifests live under `examples/`:

- `risky-web.yaml`
- `hardened-web.yaml`

The web UI can also load API-provided examples directly.

## How Podscope fits into OpsDeck

Podscope is intended to become the Kubernetes module that later plugs into OpsDeck. The integration path should look like this:

1. Podscope remains useful as a standalone manifest review tool.
2. OpsDeck calls Podscope analysis endpoints or imports its rule engine.
3. Findings are normalized into the shared OpsDeck finding model.
4. Reports can combine Podscope results with Dockerfile, CI/CD, IaC, SBOM, and cloud posture modules.

## Roadmap

Near-term:

- Upload file support in the browser
- SARIF export
- Markdown report export
- Severity filtering
- Rule category filtering
- Namespace and workload grouping
- Kubernetes patch generation

Later:

- Helm chart rendering and review
- Kustomize support
- Rego/OPA policy export
- Kyverno policy suggestions
- Gatekeeper constraint suggestions
- GitHub Actions pull request comments
- OpsDeck integration endpoint
- Optional kubeconfig-based cluster read-only review

## Security notes

Podscope performs static analysis on submitted YAML. Do not submit secrets or sensitive cluster configuration to untrusted deployments. If you deploy Podscope for a team, protect it behind your normal authentication layer and avoid logging submitted manifests in plaintext.

## License

No license has been selected yet. Add a license before distributing or accepting contributions.
