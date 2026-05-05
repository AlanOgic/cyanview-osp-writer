"""osp_writing tool — return OSP Writing Guide guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_text
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)


def osp_writing(text: str) -> GuidanceResult:
    validate_text(text, "osp_writing")
    resources = load_resources()
    guidance = resources.osp_guides["writing-guide"]
    logger.info("tool_call", tool="osp_writing", text_chars=len(text))
    return GuidanceResult(
        guidance=guidance,
        draft=text,
        source="osp:writing-guide",
    )
