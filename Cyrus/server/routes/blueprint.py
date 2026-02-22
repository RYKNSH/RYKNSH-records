"""Blueprint CRUD API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from models.blueprint import GrowthBlueprint, b2b_saas_template, b2c_entertainment_template

router = APIRouter(prefix="/api/blueprints", tags=["blueprints"])


class BlueprintResponse(BaseModel):
    """Blueprint API response."""

    blueprint: dict[str, Any]


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
