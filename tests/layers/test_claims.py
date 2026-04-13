"""Tests for the claims regex layer."""

from pathlib import Path

import pytest

from cyanview_osp_writer.layers.claims import ClaimsEngine
from cyanview_osp_writer.schemas import ClaimPattern, ClaimsFile


@pytest.fixture
def engine() -> ClaimsEngine:
    claims = ClaimsFile(
        version=1,
        banned_superlatives=[
            ClaimPattern(
                pattern=r"\b(industry[- ]leading|revolutionary)\b",
                severity="high",
                reason="vague superlative",
            ),
            ClaimPattern(
                pattern=r"\b(seamless|magical)\b",
                severity="medium",
                reason="feel-good adjective",
            ),
        ],
        technical_claims_needing_source=[
            ClaimPattern(
                pattern=r"\bzero[- ]latency\b",
                severity="high",
                reason="physically impossible",
            ),
            ClaimPattern(
                pattern=r"\b100%\s+compatible\b",
                severity="high",
                reason="absolute claim",
            ),
        ],
        require_sourcing_topics=["latency numbers"],
    )
    return ClaimsEngine(claims)


class TestClaimsEngine:
    def test_clean_draft_no_hits(self, engine: ClaimsEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "clean.md").read_text()
        assert engine.scan(text) == []

    def test_violations_draft_detects_all_categories(
        self, engine: ClaimsEngine, fixtures_dir: Path
    ):
        text = (fixtures_dir / "drafts" / "claims_violations.md").read_text()
        hits = engine.scan(text)
        matched = {h.matched_text.lower() for h in hits}
        assert "industry-leading" in matched
        assert "revolutionary" in matched
        assert "zero-latency" in matched
        assert "100% compatible" in matched
        assert "seamless" in matched
        assert "magical" in matched

    def test_hit_carries_severity_and_category(self, engine: ClaimsEngine):
        hits = engine.scan("This is revolutionary.")
        assert len(hits) == 1
        h = hits[0]
        assert h.severity == "high"
        assert h.category == "banned_superlative"
        assert h.reason == "vague superlative"

    def test_technical_category(self, engine: ClaimsEngine):
        hits = engine.scan("zero latency for everyone")
        assert len(hits) == 1
        assert hits[0].category == "technical_claim"

    def test_offsets_correct(self, engine: ClaimsEngine):
        text = "It is revolutionary technology."
        hits = engine.scan(text)
        assert text[hits[0].start : hits[0].end] == "revolutionary"
