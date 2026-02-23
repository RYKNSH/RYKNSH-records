"""Growth pipeline API routes — Full 23-node pipeline access."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from engine.graph import run_growth, run_intelligence
from server.tenant import Tenant, authenticate, check_plan_access

router = APIRouter(prefix="/api/growth", tags=["growth"])


class GrowthRequest(BaseModel):
    """Request body for growth pipeline execution."""

    blueprint: dict[str, Any]


class GrowthResponse(BaseModel):
    """Response from growth pipeline execution."""

    # Intelligence
    market_data: dict[str, Any] = {}
    icp_profiles: list[dict[str, Any]] = []
    detected_signals: list[dict[str, Any]] = []

    # Trust
    trust_scores: dict[str, Any] = {}

    # Acquisition
    outbound_status: str = ""
    content_plan: list[dict[str, Any]] = []
    campaign: dict[str, Any] = {}
    ad_plan: dict[str, Any] = {}

    # Conversion (dynamic — only populated for the selected pipeline)
    nurture_sequence: dict[str, Any] = {}
    proposal: dict[str, Any] = {}
    close_strategy: dict[str, Any] = {}
    activation: dict[str, Any] = {}
    monetization: dict[str, Any] = {}
    marketplace_strategy: dict[str, Any] = {}

    # Evolution
    performance_metrics: dict[str, Any] = {}
    optimization_actions: list[dict[str, Any]] = []

    # Meta
    node_metrics: list[dict[str, Any]] = []
    errors: list[str] = []
    pipeline_used: str = ""


@router.post("/run", response_model=GrowthResponse)
async def run_full_growth(
    request: GrowthRequest,
    tenant: Tenant = Depends(authenticate),
) -> GrowthResponse:
    """Execute the full 23-node growth pipeline.

    Requires 'usage', 'growth', or 'full_outcome' plan.
    """
    check_plan_access(tenant, "growth")

    try:
        # Inject tenant_id into blueprint
        bp = {**request.blueprint, "tenant_id": tenant.tenant_id}
        result = await run_growth(bp)

        mode = bp.get("conversion_config", {}).get("mode", bp.get("business_model", "b2b"))

        return GrowthResponse(
            market_data=result.get("market_data", {}),
            icp_profiles=result.get("icp_profiles", []),
            detected_signals=result.get("detected_signals", []),
            trust_scores=result.get("trust_scores", {}),
            outbound_status=result.get("outbound_status", ""),
            content_plan=result.get("content_plan", []),
            campaign=result.get("campaign", {}),
            ad_plan=result.get("ad_plan", {}),
            nurture_sequence=result.get("nurture_sequence", {}),
            proposal=result.get("proposal", {}),
            close_strategy=result.get("close_strategy", {}),
            activation=result.get("activation", {}),
            monetization=result.get("monetization", {}),
            marketplace_strategy=result.get("marketplace_strategy", {}),
            performance_metrics=result.get("performance_metrics", {}),
            optimization_actions=result.get("optimization_actions", []),
            node_metrics=result.get("node_metrics", []),
            errors=result.get("errors", []),
            pipeline_used=mode,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class IntelligenceOnlyResponse(BaseModel):
    """Lightweight intelligence-only response for free tier."""

    market_data: dict[str, Any] = {}
    icp_profiles: list[dict[str, Any]] = []
    detected_signals: list[dict[str, Any]] = []
    node_metrics: list[dict[str, Any]] = []
    errors: list[str] = []


@router.post("/scan", response_model=IntelligenceOnlyResponse)
async def scan_intelligence(
    request: GrowthRequest,
    tenant: Tenant = Depends(authenticate),
) -> IntelligenceOnlyResponse:
    """Run Intelligence Layer only (available on all plans)."""
    check_plan_access(tenant, "intelligence")

    try:
        bp = {**request.blueprint, "tenant_id": tenant.tenant_id}
        result = await run_intelligence(bp)
        return IntelligenceOnlyResponse(
            market_data=result.get("market_data", {}),
            icp_profiles=result.get("icp_profiles", []),
            detected_signals=result.get("detected_signals", []),
            node_metrics=result.get("node_metrics", []),
            errors=result.get("errors", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
