"""Tests for the osp_seo tool."""

from cyanview_osp_writer.tools.models import GuidanceResult
from cyanview_osp_writer.tools.osp_seo import osp_seo


class TestOspSeo:
    def test_no_keywords(self):
        r = osp_seo("Some draft text.")
        assert isinstance(r, GuidanceResult)
        assert r.source == "osp:seo-guide"
        assert (
            "target keywords" not in r.guidance.lower()
            or "(none)" in r.guidance.lower()
        )

    def test_with_keywords(self):
        r = osp_seo("Some draft.", target_keywords=["camera control", "broadcast"])
        assert "camera control" in r.guidance
        assert "broadcast" in r.guidance
