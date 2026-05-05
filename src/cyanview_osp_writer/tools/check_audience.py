"""check_audience tool — assemble audience-aware review prompt."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._validation import validate_audience, validate_text
from cyanview_osp_writer.layers.audience import AudienceLayer
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)


def check_audience(text: str, audience: str) -> GuidanceResult:
    validate_audience(audience)
    validate_text(text, "check_audience")
    resources = load_resources()
    layer = AudienceLayer(resources.audiences)
    review = layer.assemble(text, audience=audience)
    logger.info(
        "tool_call",
        tool="check_audience",
        audience=audience,
        text_chars=len(text),
    )
    return GuidanceResult(
        guidance=review.guidance,
        draft=text,
        source=f"cyanview:audience:{audience}",
    )
