"""Cyrus FastAPI application — Full PLG API."""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from server.routes.intelligence import router as intelligence_router
from server.routes.blueprint import router as blueprint_router
from server.routes.growth import router as growth_router
from server.routes.tenants import router as tenants_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

app = FastAPI(
    title="Cyrus Growth Engine",
    description=(
        "Autonomous Full-Funnel Growth Engine — B2B/B2C/C2C.\n\n"
        "23 nodes across 4 layers: Intelligence → Trust → Acquisition → Conversion → Evolution.\n\n"
        "## Plans\n"
        "- **Free**: Intelligence Layer only (100 scans/mo)\n"
        "- **Usage**: Full pipeline, pay per run\n"
        "- **Growth**: Full pipeline + performance bonuses\n"
        "- **Full Outcome**: Unlimited, pay only on results"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(intelligence_router)
app.include_router(blueprint_router)
app.include_router(growth_router)
app.include_router(tenants_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "cyrus",
        "version": "1.0.0",
        "nodes": "23",
        "layers": "4",
    }


@app.get("/")
async def root():
    """Redirect to landing page."""
    return RedirectResponse(url="/static/index.html")


# Mount static files
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

