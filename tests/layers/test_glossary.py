"""Tests for the glossary regex layer."""

from pathlib import Path

import pytest

from cyanview_osp_writer.layers.glossary import GlossaryEngine
from cyanview_osp_writer.schemas import GlossaryFile, GlossaryTerm


@pytest.fixture
def engine() -> GlossaryEngine:
    glossary = GlossaryFile(
        version=1,
        terms=[
            GlossaryTerm(
                canonical="RCP",
                accept=["RCP", "Remote Control Panel"],
                reject=["remote panel", "control pad"],
            ),
            GlossaryTerm(
                canonical="Cyanview",
                accept=["Cyanview"],
                reject=["CyanView", "cyanview"],
            ),
            GlossaryTerm(
                canonical="RIO Live",
                accept=["RIO Live"],
                reject=["RioLive", "Rio Live"],
            ),
        ],
    )
    return GlossaryEngine(glossary)


class TestGlossaryEngine:
    def test_clean_draft_no_hits(self, engine: GlossaryEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "clean.md").read_text()
        hits = engine.scan(text)
        assert hits == []

    def test_violations_detected(self, engine: GlossaryEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "glossary_violations.md").read_text()
        hits = engine.scan(text)
        canonicals = {h.canonical for h in hits}
        assert "Cyanview" in canonicals
        assert "RCP" in canonicals
        assert "RIO Live" in canonicals

    def test_hit_includes_offset_and_match(self, engine: GlossaryEngine):
        text = "We sell a remote panel and a control pad."
        hits = engine.scan(text)
        assert len(hits) == 2
        rp = next(h for h in hits if h.matched_text == "remote panel")
        assert rp.canonical == "RCP"
        assert text[rp.start : rp.end] == "remote panel"

    def test_case_insensitive_reject(self, engine: GlossaryEngine):
        hits = engine.scan("REMOTE PANEL")
        assert len(hits) == 1
        assert hits[0].canonical == "RCP"

    def test_case_sensitive_canonical_distinction(self, engine: GlossaryEngine):
        # "CyanView" is rejected, "Cyanview" is accepted — they differ only in case
        hits = engine.scan("CyanView is wrong but Cyanview is fine.")
        assert len(hits) == 1
        assert hits[0].matched_text == "CyanView"

    def test_word_boundary(self, engine: GlossaryEngine):
        # "remote panel" inside a longer non-word context still matches.
        # But "controlpad" (no space) should NOT match "control pad".
        hits = engine.scan("controlpad")
        assert hits == []

    def test_skip_code_blocks(self, engine: GlossaryEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "with_code_blocks.md").read_text()
        hits = engine.scan(text)
        # Only the "remote panel" outside the code block should be flagged.
        assert len(hits) == 1
        assert hits[0].matched_text == "remote panel"
        # And it should be after the code block close.
        assert hits[0].start > text.index("```\n\nBut")
