"""check_glossary tool — deterministic glossary scan."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_text
from cyanview_osp_writer.layers.glossary import GlossaryEngine
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GlossaryHitOut, GlossaryResult

logger = structlog.get_logger(__name__)


def check_glossary(text: str) -> GlossaryResult:
    validate_text(text, "check_glossary")
    resources = load_resources()
    engine = GlossaryEngine(resources.glossary)
    try:
        hits = engine.scan(text)
    except TimeoutError as exc:
        raise ValueError(
            f"regex_timeout: glossary scan exceeded the per-pattern timeout. "
            f"Detail: {exc}"
        ) from exc
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
