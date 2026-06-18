from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai import provider_status
from app.api.routes import router
from app.core.settings import get_settings

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Static Kubernetes manifest review for platform, SRE, and DevSecOps teams.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "podscope", "version": settings.app_version}


@app.get("/ready")
def ready() -> dict[str, object]:
    return {"status": "ready", "ai": provider_status()}
