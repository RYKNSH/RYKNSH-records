"""Intelligence Layer API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.graph import run_intelligence

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


class ScanRequest(BaseModel):
    """Request body for intelligence scan."""

    blueprint: dict[str, Any]


class ScanResponse(BaseModel):
    """Response from intelligence scan."""

    market_data: dict[str, Any] = {}
    icp_profiles: list[dict[str, Any]] = []
    detected_signals: list[dict[str, Any]] = []
    node_metrics: list[dict[str, Any]] = []
    errors: list[str] = []


@router.post("/scan", response_model=ScanResponse)
async def scan(request: ScanRequest) -> ScanResponse:
    """Run the Intelligence Layer pipeline.

    Takes a GrowthBlueprint and returns market data, ICP profiles,
    and detected signals.
    """
    try:
        result = await run_intelligence(request.blueprint)
        return ScanResponse(
            market_data=result.get("market_data", {}),
            icp_profiles=result.get("icp_profiles", []),
            detected_signals=result.get("detected_signals", []),
            node_metrics=result.get("node_metrics", []),
            errors=result.get("errors", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
