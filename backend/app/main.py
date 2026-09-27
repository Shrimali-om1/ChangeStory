"""
main.py — ChangeStory FastAPI application entry point.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analyze import router as analyze_router
from app.routes.reports import router as reports_router
from app.routes.scenarios import router as scenarios_router

app = FastAPI(
    title="ChangeStory API",
    description=(
        "Local-first tool for understanding changes to Python Git repositories. "
        "See /docs for interactive API documentation."
    ),
    version="0.1.0",
)

# Allow the Next.js dev server and production build to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_PREFIX = "/api/v1"

app.include_router(analyze_router, prefix=_PREFIX, tags=["Analysis"])
app.include_router(reports_router, prefix=_PREFIX, tags=["Reports"])
app.include_router(scenarios_router, prefix=_PREFIX, tags=["Scenarios & Verify"])


@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    return {
        "service": "ChangeStory API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
