"""osp_meta tool — return OSP Meta-information guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_text
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)


def osp_meta(text: str) -> GuidanceResult:
    validate_text(text, "osp_meta")
    resources = load_resources()
    guidance = resources.osp_guides["meta-guide"]
    logger.info("tool_call", tool="osp_meta", text_chars=len(text))
    return GuidanceResult(guidance=guidance, draft=text, source="osp:meta-guide")
