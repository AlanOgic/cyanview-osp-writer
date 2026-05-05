"""Tests for the osp_edit tool."""

import pytest

from cyanview_osp_writer._constants import MAX_TEXT_CHARS
from cyanview_osp_writer.tools.models import GuidanceResult
from cyanview_osp_writer.tools.osp_edit import osp_edit


class TestOspEdit:
    def test_returns_guidance_with_draft(self):
        r = osp_edit("Some draft text.")
        assert isinstance(r, GuidanceResult)
        assert r.draft == "Some draft text."
        assert r.source == "osp:editing-codes"
        assert len(r.guidance) > 0
        assert "placeholder" in r.guidance.lower() or "editing" in r.guidance.lower()

    def test_text_too_long(self):
        with pytest.raises(ValueError, match="text_too_long"):
            osp_edit("x" * (MAX_TEXT_CHARS + 1))
