"""Tests for Entity Model v3."""

from models.entity import (
    Creator,
    CreatorDomain,
    Individual,
    IndividualContext,
    Industry,
    Organization,
    OrgSize,
    Signal,
    create_entity,
)


class TestSignal:
    def test_signal_creation(self):
        s = Signal(type="hiring_engineer", source="linkedin", confidence=0.85)
        assert s.type == "hiring_engineer"
        assert s.source == "linkedin"
        assert s.confidence == 0.85

    def test_signal_confidence_bounds(self):
        s = Signal(type="test", source="test", confidence=0.0)
        assert s.confidence == 0.0
        s = Signal(type="test", source="test", confidence=1.0)
        assert s.confidence == 1.0


class TestOrganization:
    def test_defaults(self):
        org = Organization()
        assert org.entity_type == "organization"
        assert org.industry == Industry.OTHER
        assert org.size == OrgSize.MID
        assert org.signals == []

    def test_full_creation(self):
        org = Organization(
            industry=Industry.SAAS,
            size=OrgSize.ENTERPRISE,
            name="Acme Corp",
            tech_stack=["python", "react"],
            signals=[Signal(type="hiring", source="linkedin", confidence=0.9)],
        )
        assert org.industry == Industry.SAAS
        assert org.name == "Acme Corp"
        assert len(org.signals) == 1


class TestIndividual:
    def test_defaults(self):
        ind = Individual()
        assert ind.entity_type == "individual"
        assert ind.context == IndividualContext.OTHER

    def test_fan_creation(self):
        ind = Individual(
            context=IndividualContext.FAN,
            interests=["hiphop", "indie"],
            values=["authenticity"],
        )
        assert ind.context == IndividualContext.FAN
        assert "hiphop" in ind.interests


class TestCreator:
    def test_defaults(self):
        c = Creator()
        assert c.entity_type == "creator"
        assert c.domain == CreatorDomain.OTHER
        assert c.output_quality_score == 0.0

    def test_musician_creation(self):
        c = Creator(
            domain=CreatorDomain.MUSICIAN,
            output_quality_score=0.85,
            audience_size=50000,
        )
        assert c.domain == CreatorDomain.MUSICIAN
        assert c.audience_size == 50000


class TestEntityFactory:
    def test_create_organization(self):
        e = create_entity("organization", industry="saas")
        assert isinstance(e, Organization)

    def test_create_individual(self):
        e = create_entity("individual", context="fan")
        assert isinstance(e, Individual)

    def test_create_creator(self):
        e = create_entity("creator", domain="musician")
        assert isinstance(e, Creator)

    def test_invalid_type(self):
        try:
            create_entity("invalid_type")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass
