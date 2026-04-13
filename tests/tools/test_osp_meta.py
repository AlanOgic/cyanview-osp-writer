"""Tests for the osp_meta tool."""

from cyanview_osp_writer.tools.models import GuidanceResult
from cyanview_osp_writer.tools.osp_meta import osp_meta


class TestOspMeta:
    def test_returns_guidance_and_draft(self):
        r = osp_meta("Draft body.")
        assert isinstance(r, GuidanceResult)
        assert r.source == "osp:meta-guide"
        assert r.draft == "Draft body."
