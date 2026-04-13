"""check_audience tool — assemble audience-aware review prompt."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.layers.audience import AudienceLayer
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)

VALID_AUDIENCES = {"dp", "broadcast_engineer", "rental_house", "mixed"}
MAX_TEXT_CHARS = 50_000


def check_audience(text: str, audience: str) -> GuidanceResult:
    if audience not in VALID_AUDIENCES:
        raise ValueError(
            f"invalid_audience: {audience!r}; must be one of {sorted(VALID_AUDIENCES)}"
        )
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call check_audience per section."
        )
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
