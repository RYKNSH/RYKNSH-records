"""Blueprint CRUD API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.blueprint import (
    GrowthBlueprint,
    b2b_saas_template,
    b2c_entertainment_template,
    RYKNSH_TEMPLATES,
)

router = APIRouter(prefix="/api/blueprints", tags=["blueprints"])


class BlueprintResponse(BaseModel):
    """Blueprint API response."""

    blueprint: dict[str, Any]


class TemplateListResponse(BaseModel):
    """Available templates."""

    templates: list[dict[str, str]]


@router.get("/templates/b2b-saas")
async def get_b2b_template() -> BlueprintResponse:
    """Get the B2B SaaS growth blueprint template."""
    bp = b2b_saas_template("demo-tenant")
    return BlueprintResponse(blueprint=bp.model_dump())


@router.get("/templates/b2c-entertainment")
async def get_b2c_template() -> BlueprintResponse:
    """Get the B2C entertainment growth blueprint template."""
    bp = b2c_entertainment_template("demo-tenant")
    return BlueprintResponse(blueprint=bp.model_dump())


@router.get("/templates/ryknsh")
async def list_ryknsh_templates() -> TemplateListResponse:
    """List all RYKNSH subsidiary blueprint templates."""
    templates = []
    for key, fn in RYKNSH_TEMPLATES.items():
        bp = fn("demo")
        templates.append({
            "id": key,
            "name": bp.name,
            "business_model": bp.business_model.value,
            "pricing_model": bp.pricing_model,
        })
    return TemplateListResponse(templates=templates)


@router.get("/templates/ryknsh/{subsidiary}")
async def get_ryknsh_template(subsidiary: str) -> BlueprintResponse:
    """Get a specific RYKNSH subsidiary blueprint template."""
    fn = RYKNSH_TEMPLATES.get(subsidiary)
    if not fn:
        raise HTTPException(status_code=404, detail=f"Template '{subsidiary}' not found. Available: {list(RYKNSH_TEMPLATES.keys())}")
    bp = fn("demo-tenant")
    return BlueprintResponse(blueprint=bp.model_dump())

