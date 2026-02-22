"""Cyrus FastAPI application."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes.intelligence import router as intelligence_router
from server.routes.blueprint import router as blueprint_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

app = FastAPI(
    title="Cyrus Growth Engine",
    description="Autonomous Full-Funnel Growth Engine — B2B/B2C/C2C",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(intelligence_router)
app.include_router(blueprint_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "cyrus"}
