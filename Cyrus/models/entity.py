"""Cyrus Entity Model v3 — Universal target abstraction.

Supports all industries and business models through enum-based
parameterization: Organization (B2B), Individual (B2C), Creator (C2C).
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Industry(str, Enum):
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    FINANCE = "finance"
    ENTERTAINMENT = "entertainment"
    MANUFACTURING = "manufacturing"
    REAL_ESTATE = "real_estate"
    OTHER = "other"


class OrgSize(str, Enum):
    SOLO = "solo"
    SMALL = "small"
    MID = "mid"
    ENTERPRISE = "enterprise"


class IndividualContext(str, Enum):
    BUYER = "buyer"
    FAN = "fan"
    STUDENT = "student"
    PATIENT = "patient"
    SUBSCRIBER = "subscriber"
    MEMBER = "member"
    OTHER = "other"


class CreatorDomain(str, Enum):
    MUSICIAN = "musician"
    DEVELOPER = "developer"
    DESIGNER = "designer"
    WRITER = "writer"
    EDUCATOR = "educator"
    CONSULTANT = "consultant"
    OTHER = "other"


class BusinessModel(str, Enum):
    B2B = "b2b"
    B2C = "b2c"
    C2C = "c2c"


class DealComplexity(str, Enum):
    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"


# ---------------------------------------------------------------------------
# Signal (unified across all Entity types)
# ---------------------------------------------------------------------------

class Signal(BaseModel):
    """A detected signal indicating purchase/engagement intent."""

    type: str = Field(..., description="Signal type, e.g. 'hiring_engineer', 'playlist_add'")
    source: str = Field(..., description="Data source, e.g. 'linkedin', 'spotify'")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Decision Maker (for Organization)
# ---------------------------------------------------------------------------

class DecisionMaker(BaseModel):
    """A key decision maker within an Organization."""

    role: str
    name: str | None = None
    personality_profile: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Entity Types
# ---------------------------------------------------------------------------

class Entity(BaseModel):
    """Abstract base for all target entities."""

    entity_id: str | None = None
    tenant_id: str | None = None
    signals: list[Signal] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Organization(Entity):
    """B2B target — any organization (company, institution, etc.)."""

    entity_type: str = "organization"
    industry: Industry = Industry.OTHER
    size: OrgSize = OrgSize.MID
    name: str | None = None
    decision_makers: list[DecisionMaker] = Field(default_factory=list)
    tech_stack: list[str] = Field(default_factory=list)
    funding_stage: str | None = None
    employee_count: int | None = None


class Individual(Entity):
    """B2C target — any individual person."""

    entity_type: str = "individual"
    context: IndividualContext = IndividualContext.OTHER
    demographics: dict[str, Any] = Field(default_factory=dict)
    psychographics: dict[str, Any] = Field(default_factory=dict)
    interests: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)


class Creator(Entity):
    """C2C target — any creator/producer."""

    entity_type: str = "creator"
    domain: CreatorDomain = CreatorDomain.OTHER
    output_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    audience_size: int = 0
    platform_profiles: dict[str, str] = Field(default_factory=dict)
    collaboration_history: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_entity(entity_type: str, **kwargs: Any) -> Entity:
    """Factory to create the correct Entity subclass."""
    constructors = {
        "organization": Organization,
        "individual": Individual,
        "creator": Creator,
    }
    cls = constructors.get(entity_type)
    if cls is None:
        raise ValueError(f"Unknown entity type: {entity_type}. Must be one of {list(constructors)}")
    return cls(**kwargs)
