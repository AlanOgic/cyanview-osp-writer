"""Tests for shared tool output models."""

from cyanview_osp_writer.tools.models import (
    ClaimsHitOut,
    ClaimsResult,
    GlossaryHitOut,
    GlossaryResult,
    GuidanceResult,
    ReviewBrief,
    ReviewSection,
)


class TestModels:
    def test_glossary_hit_out(self):
        h = GlossaryHitOut(
            canonical="RCP", matched_text="remote panel", start=10, end=22, note=None
        )
        assert h.canonical == "RCP"

    def test_glossary_result(self):
        r = GlossaryResult(hits=[], summary="No glossary issues found.")
        assert r.hits == []

    def test_claims_hit_out(self):
        h = ClaimsHitOut(
            matched_text="industry-leading",
            start=0,
            end=16,
            category="banned_superlative",
            severity="high",
            reason="vague",
        )
        assert h.severity == "high"

    def test_claims_result(self):
        r = ClaimsResult(
            hits=[],
            require_sourcing_topics=["latency"],
            summary="No issues.",
        )
        assert r.require_sourcing_topics == ["latency"]

    def test_guidance_result(self):
        g = GuidanceResult(guidance="prompt", draft="text", source="osp:editing-codes")
        assert g.source == "osp:editing-codes"

    def test_review_brief_serialization(self):
        brief = ReviewBrief(
            audience="dp",
            content_type="blog_post",
            osp_source_sha="abc123",
            execution_plan=["1. glossary", "2. audience"],
            sections=[
                ReviewSection(name="glossary", payload={"hits": []}),
            ],
        )
        d = brief.model_dump()
        assert d["audience"] == "dp"
        assert d["sections"][0]["name"] == "glossary"
