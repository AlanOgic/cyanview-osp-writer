"""Tests for the review_draft orchestrator."""

from pathlib import Path

import pytest

from cyanview_osp_writer.tools.models import ReviewBrief
from cyanview_osp_writer.tools.review_draft import (
    VALID_AUDIENCES,
    VALID_CONTENT_TYPES,
    review_draft,
)


class TestReviewDraft:
    def test_returns_review_brief(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="broadcast_engineer", content_type="blog_post"
        )
        assert isinstance(brief, ReviewBrief)
        assert brief.audience == "broadcast_engineer"
        assert brief.content_type == "blog_post"
        assert len(brief.sections) > 0

    def test_sections_in_expected_order(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        names = [s.name for s in brief.sections]
        assert names == [
            "glossary",
            "claims",
            "audience",
            "osp_edit",
            "osp_seo",
            "osp_meta",
        ]

    def test_glossary_section_contains_hits(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        glossary = next(s for s in brief.sections if s.name == "glossary")
        assert glossary.payload["hits"]
        canonicals = {h["canonical"] for h in glossary.payload["hits"]}
        assert "Cyanview" in canonicals

    def test_claims_section_contains_hits(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        claims = next(s for s in brief.sections if s.name == "claims")
        matched = {h["matched_text"].lower() for h in claims.payload["hits"]}
        assert "industry-leading" in matched or "revolutionary" in matched

    def test_audience_section_contains_guidance(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="broadcast_engineer", content_type="blog_post"
        )
        audience = next(s for s in brief.sections if s.name == "audience")
        assert "Broadcast" in audience.payload["guidance"]

    def test_focus_filters_sections(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text,
            audience="dp",
            content_type="blog_post",
            focus=["glossary", "claims"],
        )
        names = {s.name for s in brief.sections}
        assert names == {"glossary", "claims"}

    def test_invalid_audience_rejected(self):
        with pytest.raises(ValueError, match="invalid_audience"):
            review_draft(text="x", audience="director", content_type="blog_post")

    def test_invalid_content_type_rejected(self):
        with pytest.raises(ValueError, match="invalid_content_type"):
            review_draft(text="x", audience="dp", content_type="tweet")

    def test_invalid_focus_rejected(self):
        with pytest.raises(ValueError, match="invalid_focus"):
            review_draft(
                text="x", audience="dp", content_type="blog_post", focus=["typos"]
            )

    def test_text_too_long(self):
        with pytest.raises(ValueError, match="text_too_long"):
            review_draft(
                text="x" * 60_000, audience="dp", content_type="blog_post"
            )

    def test_execution_plan_present(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        assert len(brief.execution_plan) >= 1
        assert all(isinstance(s, str) for s in brief.execution_plan)

    def test_constants_exposed(self):
        assert "dp" in VALID_AUDIENCES
        assert "blog_post" in VALID_CONTENT_TYPES
