"""osp_meta tool — return OSP Meta-information guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def osp_meta(text: str) -> GuidanceResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call osp_meta per section."
        )
    resources = load_resources()
    guidance = resources.osp_guides["meta-guide"]
    logger.info("tool_call", tool="osp_meta", text_chars=len(text))
    return GuidanceResult(guidance=guidance, draft=text, source="osp:meta-guide")
