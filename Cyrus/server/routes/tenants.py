"""Tenant management API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from server.tenant import create_tenant, get_tenant, PLAN_LIMITS

router = APIRouter(prefix="/api/tenants", tags=["tenants"])


class CreateTenantRequest(BaseModel):
    """Request body for creating a tenant."""

    tenant_id: str
    name: str
    plan: str = "free"


class CreateTenantResponse(BaseModel):
    """Response after creating a tenant."""

    tenant_id: str
    name: str
    plan: str
    api_key: str  # Only returned on creation
    plan_limits: dict


@router.post("/", response_model=CreateTenantResponse)
async def create(request: CreateTenantRequest) -> CreateTenantResponse:
    """Create a new tenant and return their API key."""
    existing = get_tenant(request.tenant_id)
    if existing:
        raise HTTPException(status_code=409, detail="Tenant already exists")

    tenant, api_key = create_tenant(request.tenant_id, request.name, request.plan)
    limits = PLAN_LIMITS.get(tenant.plan, PLAN_LIMITS["free"])

    return CreateTenantResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        plan=tenant.plan,
        api_key=api_key,
        plan_limits=limits,
    )


class TenantInfoResponse(BaseModel):
    """Public tenant info (no API key)."""

    tenant_id: str
    name: str
    plan: str
    plan_limits: dict


@router.get("/{tenant_id}", response_model=TenantInfoResponse)
async def get_info(tenant_id: str) -> TenantInfoResponse:
    """Get tenant info by ID."""
    tenant = get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    limits = PLAN_LIMITS.get(tenant.plan, PLAN_LIMITS["free"])
    return TenantInfoResponse(
        tenant_id=tenant.tenant_id,
        name=tenant.name,
        plan=tenant.plan,
        plan_limits=limits,
    )


class PlanResponse(BaseModel):
    """Available plans."""

    plans: dict


@router.get("/plans/available")
async def get_plans() -> PlanResponse:
    """List all available plans and their limits."""
    return PlanResponse(plans=PLAN_LIMITS)
