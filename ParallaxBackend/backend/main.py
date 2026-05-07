from __future__ import annotations

import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.endpoints import accounts, automations, integrations, trading212
from backend.core.config import settings
from backend.db.database import Database


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = str(uuid4())
    started = time.time()
    response = await call_next(request)
    response.headers["X-Parallax-Request-Id"] = request_id
    response.headers["X-Parallax-Duration-Ms"] = f"{(time.time() - started) * 1000:.2f}"
    return response


@app.on_event("startup")
async def startup() -> None:
    app.state.db = Database(settings.DB_PATH)
    app.state.db.init_schema()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Parallax API",
        "docs": f"{settings.API_V1_STR}/openapi.json",
    }


@app.get(f"{settings.API_V1_STR}/health")
async def health():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "db_path": settings.DB_PATH,
    }


app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_STR}/accounts",
    tags=["accounts"],
)
app.include_router(
    trading212.router,
    prefix=f"{settings.API_V1_STR}/trading212",
    tags=["trading212"],
)
app.include_router(
    integrations.router,
    prefix=f"{settings.API_V1_STR}/integrations",
    tags=["integrations"],
)
app.include_router(
    automations.router,
    prefix=f"{settings.API_V1_STR}/automations",
    tags=["automations"],
)
