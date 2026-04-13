"""Tests for pydantic schemas validating bundled YAML resources."""

import pytest
from pydantic import ValidationError

from cyanview_osp_writer.schemas import (
    AudienceProfile,
    AudiencesFile,
    ClaimPattern,
    ClaimsFile,
    GlossaryFile,
    GlossaryTerm,
)


class TestGlossaryTerm:
    def test_minimal_term_valid(self):
        term = GlossaryTerm(canonical="RCP", reject=["remote panel"])
        assert term.canonical == "RCP"
        assert term.reject == ["remote panel"]
        assert term.accept == []
        assert term.deprecated_aliases == []
        assert term.note is None

    def test_full_term_valid(self):
        term = GlossaryTerm(
            canonical="RIO Live",
            full_name="RIO Live system",
            accept=["RIO Live", "RIO-Live"],
            reject=["RioLive"],
            deprecated_aliases=["Rio"],
            note="Always capitalize",
        )
        assert term.full_name == "RIO Live system"

    def test_canonical_required(self):
        with pytest.raises(ValidationError):
            GlossaryTerm(reject=["x"])


class TestGlossaryFile:
    def test_valid(self):
        f = GlossaryFile(version=1, terms=[GlossaryTerm(canonical="RCP")])
        assert f.version == 1
        assert len(f.terms) == 1

    def test_version_must_be_one(self):
        with pytest.raises(ValidationError):
            GlossaryFile(version=2, terms=[])


class TestAudienceProfile:
    def test_valid(self):
        p = AudienceProfile(
            label="DP",
            assumes=["cinematic language"],
            avoid=["jargon"],
            tone="creative",
        )
        assert p.label == "DP"


class TestAudiencesFile:
    def test_three_required_audiences(self):
        f = AudiencesFile(
            version=1,
            audiences={
                "dp": AudienceProfile(label="DP", assumes=[], avoid=[], tone="x"),
                "broadcast_engineer": AudienceProfile(
                    label="BE", assumes=[], avoid=[], tone="x"
                ),
                "rental_house": AudienceProfile(
                    label="RH", assumes=[], avoid=[], tone="x"
                ),
            },
        )
        assert set(f.audiences.keys()) == {"dp", "broadcast_engineer", "rental_house"}

    def test_missing_audience_rejected(self):
        with pytest.raises(ValidationError):
            AudiencesFile(
                version=1,
                audiences={
                    "dp": AudienceProfile(label="DP", assumes=[], avoid=[], tone="x")
                },
            )


class TestClaimPattern:
    def test_valid(self):
        c = ClaimPattern(
            pattern=r"\bindustry-leading\b", severity="high", reason="vague"
        )
        assert c.severity == "high"

    def test_invalid_regex_rejected(self):
        with pytest.raises(ValidationError):
            ClaimPattern(pattern="[unclosed", severity="high", reason="bad")

    def test_severity_enum(self):
        with pytest.raises(ValidationError):
            ClaimPattern(pattern="x", severity="critical", reason="r")


class TestClaimsFile:
    def test_valid(self):
        f = ClaimsFile(
            version=1,
            banned_superlatives=[
                ClaimPattern(pattern="x", severity="high", reason="r")
            ],
            technical_claims_needing_source=[],
            require_sourcing_topics=["latency"],
        )
        assert len(f.banned_superlatives) == 1
