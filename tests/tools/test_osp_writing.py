"""Tests for the osp_writing tool."""

import pytest

from cyanview_osp_writer._constants import MAX_TEXT_CHARS
from cyanview_osp_writer.tools.models import GuidanceResult
from cyanview_osp_writer.tools.osp_writing import osp_writing


class TestOspWriting:
    def test_returns_guidance_with_draft(self):
        r = osp_writing("Some draft text.")
        assert isinstance(r, GuidanceResult)
        assert r.draft == "Some draft text."
        assert r.source == "osp:writing-guide"
        assert len(r.guidance) > 0

    def test_text_too_long(self):
        with pytest.raises(ValueError, match="text_too_long"):
            osp_writing("x" * (MAX_TEXT_CHARS + 1))
