"""check_claims tool — deterministic claims scan."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_text
from cyanview_osp_writer.layers.claims import ClaimsEngine
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import ClaimsHitOut, ClaimsResult

logger = structlog.get_logger(__name__)


def check_claims(text: str) -> ClaimsResult:
    validate_text(text, "check_claims")
    resources = load_resources()
    engine = ClaimsEngine(resources.claims)
    hits = engine.scan(text)
    out = [
        ClaimsHitOut(
            matched_text=h.matched_text,
            start=h.start,
            end=h.end,
            category=h.category,
            severity=h.severity,
            reason=h.reason,
        )
        for h in hits
    ]
    summary = (
        "No claims issues found."
        if not out
        else f"Found {len(out)} claim issue(s) — review severity high items first."
    )
    logger.info("tool_call", tool="check_claims", text_chars=len(text), hits=len(out))
    return ClaimsResult(
        hits=out,
        require_sourcing_topics=engine.require_sourcing_topics,
        summary=summary,
    )
