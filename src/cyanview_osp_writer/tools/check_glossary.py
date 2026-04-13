"""check_glossary tool — deterministic glossary scan."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.layers.glossary import GlossaryEngine
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GlossaryHitOut, GlossaryResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def check_glossary(text: str) -> GlossaryResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call check_glossary per section."
        )
    resources = load_resources()
    engine = GlossaryEngine(resources.glossary)
    hits = engine.scan(text)
    out = [
        GlossaryHitOut(
            canonical=h.canonical,
            matched_text=h.matched_text,
            start=h.start,
            end=h.end,
            note=h.note,
        )
        for h in hits
    ]
    summary = (
        "No glossary issues found."
        if not out
        else f"Found {len(out)} glossary issue(s) — see hits for details."
    )
    logger.info("tool_call", tool="check_glossary", text_chars=len(text), hits=len(out))
    return GlossaryResult(hits=out, summary=summary)
