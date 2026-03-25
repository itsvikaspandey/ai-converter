from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.clips import router as clips_router
from backend.api.jobs import router as jobs_router
from backend.config import get_settings
from backend.db.session import Base, engine


settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(jobs_router, prefix=settings.api_prefix)
app.include_router(clips_router, prefix=settings.api_prefix)
app.mount("/storage", StaticFiles(directory=str(settings.storage_root)), name="storage")


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
