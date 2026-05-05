"""osp_seo tool — return OSP On-Page SEO guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_text
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)


def osp_seo(
    text: str, target_keywords: list[str] | None = None
) -> GuidanceResult:
    validate_text(text, "osp_seo")
    resources = load_resources()
    base_guidance = resources.osp_guides["seo-guide"]
    keywords_block = (
        f"\n\nTarget keywords: {', '.join(target_keywords)}\n"
        if target_keywords
        else "\n\nTarget keywords: (none) — infer from draft topic\n"
    )
    guidance = base_guidance + keywords_block
    logger.info(
        "tool_call",
        tool="osp_seo",
        text_chars=len(text),
        keywords=len(target_keywords or []),
    )
    return GuidanceResult(guidance=guidance, draft=text, source="osp:seo-guide")
