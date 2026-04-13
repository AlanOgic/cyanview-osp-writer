"""check_claims tool — deterministic claims scan."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.layers.claims import ClaimsEngine
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import ClaimsHitOut, ClaimsResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def check_claims(text: str) -> ClaimsResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call check_claims per section."
        )
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
