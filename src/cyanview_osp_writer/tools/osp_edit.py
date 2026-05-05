"""osp_edit tool — return OSP Editing Codes guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_text
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)


def osp_edit(text: str) -> GuidanceResult:
    validate_text(text, "osp_edit")
    resources = load_resources()
    guidance = resources.osp_guides["editing-codes"]
    logger.info("tool_call", tool="osp_edit", text_chars=len(text))
    return GuidanceResult(
        guidance=guidance,
        draft=text,
        source="osp:editing-codes",
    )
