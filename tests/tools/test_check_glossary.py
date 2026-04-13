"""Tests for the check_glossary tool."""

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.check_glossary import check_glossary
from cyanview_osp_writer.tools.models import GlossaryResult


class TestCheckGlossary:
    def test_clean_text_returns_no_hits(self):
        result = check_glossary("The Cyanview RCP is a camera control system.")
        assert isinstance(result, GlossaryResult)
        assert result.hits == []
        assert "no glossary" in result.summary.lower()

    def test_violations_detected(self):
        result = check_glossary("The CyanView remote panel uses RioLive.")
        canonicals = {h.canonical for h in result.hits}
        assert "Cyanview" in canonicals
        assert "RCP" in canonicals
        assert "RIO Live" in canonicals
        assert str(len(result.hits)) in result.summary

    def test_resources_loaded_lazily(self):
        # Just ensure the function works without explicit setup.
        load_resources()
        check_glossary("hello")
