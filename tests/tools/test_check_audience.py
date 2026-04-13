"""Tests for the check_audience tool."""

import pytest

from cyanview_osp_writer.tools.check_audience import check_audience
from cyanview_osp_writer.tools.models import GuidanceResult


class TestCheckAudience:
    def test_dp_audience(self):
        r = check_audience("draft text", audience="dp")
        assert isinstance(r, GuidanceResult)
        assert r.draft == "draft text"
        assert "Director of Photography" in r.guidance
        assert r.source == "cyanview:audience:dp"

    def test_mixed_audience(self):
        r = check_audience("draft", audience="mixed")
        assert "Director of Photography" in r.guidance
        assert "Broadcast" in r.guidance
        assert "Rental House" in r.guidance
        assert r.source == "cyanview:audience:mixed"

    def test_invalid_audience(self):
        with pytest.raises(ValueError, match="invalid_audience"):
            check_audience("draft", audience="director")
