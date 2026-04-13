"""Tests for the bundled-resources loader."""

from cyanview_osp_writer.resources import (
    Resources,
    load_resources,
)
from cyanview_osp_writer.schemas import (
    AudiencesFile,
    ClaimsFile,
    GlossaryFile,
)


class TestLoadResources:
    def test_returns_resources_object(self):
        r = load_resources()
        assert isinstance(r, Resources)

    def test_glossary_parsed(self):
        r = load_resources()
        assert isinstance(r.glossary, GlossaryFile)
        canonicals = {t.canonical for t in r.glossary.terms}
        assert "Cyanview" in canonicals
        assert "RCP" in canonicals

    def test_audiences_parsed_with_three_keys(self):
        r = load_resources()
        assert isinstance(r.audiences, AudiencesFile)
        assert set(r.audiences.audiences.keys()) == {
            "dp",
            "broadcast_engineer",
            "rental_house",
        }

    def test_claims_parsed(self):
        r = load_resources()
        assert isinstance(r.claims, ClaimsFile)
        assert len(r.claims.banned_superlatives) > 0

    def test_osp_guidance_present(self):
        r = load_resources()
        assert "writing-guide" in r.osp_guides
        assert "editing-codes" in r.osp_guides
        assert "seo-guide" in r.osp_guides
        assert "meta-guide" in r.osp_guides
        assert "value-map" in r.osp_guides
        for content in r.osp_guides.values():
            assert isinstance(content, str)
            assert len(content) > 0

    def test_osp_source_sha_present(self):
        r = load_resources()
        assert isinstance(r.osp_source_sha, str)
        assert len(r.osp_source_sha) > 0

    def test_resources_are_cached(self):
        r1 = load_resources()
        r2 = load_resources()
        assert r1 is r2
