"""osp_value_map tool — return OSP Value Map guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_text
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)


def osp_value_map(text: str) -> GuidanceResult:
    validate_text(text, "osp_value_map")
    resources = load_resources()
    guidance = resources.osp_guides["value-map"]
    logger.info("tool_call", tool="osp_value_map", text_chars=len(text))
    return GuidanceResult(
        guidance=guidance,
        draft=text,
        source="osp:value-map",
    )
