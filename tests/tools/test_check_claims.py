"""Tests for the check_claims tool."""

import pytest

from cyanview_osp_writer._constants import MAX_TEXT_CHARS
from cyanview_osp_writer.tools.check_claims import check_claims
from cyanview_osp_writer.tools.models import ClaimsResult


class TestCheckClaims:
    def test_clean_text(self):
        r = check_claims("The Cyanview RCP supports SDI workflows.")
        assert isinstance(r, ClaimsResult)
        assert r.hits == []
        assert "latency numbers" in r.require_sourcing_topics

    def test_violations_detected(self):
        r = check_claims(
            "Our revolutionary system delivers zero-latency performance."
        )
        matched = {h.matched_text.lower() for h in r.hits}
        assert "revolutionary" in matched
        assert "zero-latency" in matched

    def test_text_too_long_raises(self):
        with pytest.raises(ValueError, match="text_too_long"):
            check_claims("x" * (MAX_TEXT_CHARS + 1))
