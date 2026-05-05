"""review_draft orchestrator — runs all six layers and returns a ReviewBrief."""

from __future__ import annotations

import structlog

from cyanview_osp_writer._constants import (
    MAX_TEXT_CHARS,
    VALID_AUDIENCES,
    VALID_CONTENT_TYPES,
    VALID_FOCUS,
)
from cyanview_osp_writer._validation import validate_audience, validate_text
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.check_audience import check_audience
from cyanview_osp_writer.tools.check_claims import check_claims
from cyanview_osp_writer.tools.check_glossary import check_glossary
from cyanview_osp_writer.tools.models import ReviewBrief, ReviewSection
from cyanview_osp_writer.tools.osp_edit import osp_edit
from cyanview_osp_writer.tools.osp_meta import osp_meta
from cyanview_osp_writer.tools.osp_seo import osp_seo

# Re-exported for callers (and tests) that import these from this module.
__all__ = [
    "MAX_TEXT_CHARS",
    "VALID_AUDIENCES",
    "VALID_CONTENT_TYPES",
    "VALID_FOCUS",
    "review_draft",
]

logger = structlog.get_logger(__name__)


_FOCUS_INSTRUCTIONS: tuple[tuple[str, str], ...] = (
    (
        "glossary",
        "Apply glossary hits inline: show each rejected term with its "
        "canonical replacement.",
    ),
    (
        "claims",
        "Apply claims hits: rewrite each high-severity superlative or "
        "unsourced technical claim.",
    ),
    (
        "audience",
        "Apply audience guidance: flag tone mismatches and "
        "assumed-knowledge gaps for the named audience.",
    ),
    (
        "osp_edit",
        "Apply OSP Editing Codes: produce a code-tagged review with "
        "before/after suggestions.",
    ),
    (
        "osp_seo",
        "Apply OSP On-Page SEO: suggest keyword integration and "
        "structure improvements.",
    ),
    (
        "osp_meta",
        "Apply OSP Meta guide: produce H1, meta title (50-60), meta "
        "description (155-160), slug.",
    ),
)


def _build_execution_plan(active: list[str], audience: str) -> list[str]:
    active_set = set(active)
    steps: list[str] = [
        "Read the structured sections below as your marching orders.",
        f"Render the review for audience={audience}.",
    ]
    steps.extend(
        instruction
        for focus, instruction in _FOCUS_INSTRUCTIONS
        if focus in active_set
    )
    steps.append("Summarise the top 3 most-impactful changes at the end.")
    return [f"{i}. {step}" for i, step in enumerate(steps, start=1)]


def review_draft(
    text: str,
    audience: str,
    content_type: str,
    focus: list[str] | None = None,
) -> ReviewBrief:
    """Run all six review layers and return a structured ReviewBrief."""
    validate_audience(audience)
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(
            f"invalid_content_type: {content_type!r}; must be one of "
            f"{sorted(VALID_CONTENT_TYPES)}"
        )
    validate_text(text, "review_draft")
    if focus is not None:
        invalid = [f for f in focus if f not in VALID_FOCUS]
        if invalid:
            raise ValueError(
                f"invalid_focus: {invalid!r}; must be subset of "
                f"{list(VALID_FOCUS)}"
            )
        active = [f for f in VALID_FOCUS if f in focus]
    else:
        active = list(VALID_FOCUS)

    resources = load_resources()
    sections: list[ReviewSection] = []

    if "glossary" in active:
        sections.append(
            ReviewSection(
                name="glossary", payload=check_glossary(text).model_dump()
            )
        )
    if "claims" in active:
        sections.append(
            ReviewSection(
                name="claims", payload=check_claims(text).model_dump()
            )
        )
    if "audience" in active:
        sections.append(
            ReviewSection(
                name="audience",
                payload=check_audience(text, audience=audience).model_dump(),
            )
        )
    if "osp_edit" in active:
        sections.append(
            ReviewSection(name="osp_edit", payload=osp_edit(text).model_dump())
        )
    if "osp_seo" in active:
        sections.append(
            ReviewSection(name="osp_seo", payload=osp_seo(text).model_dump())
        )
    if "osp_meta" in active:
        sections.append(
            ReviewSection(name="osp_meta", payload=osp_meta(text).model_dump())
        )

    brief = ReviewBrief(
        audience=audience,
        content_type=content_type,
        osp_source_sha=resources.osp_source_sha,
        execution_plan=_build_execution_plan(active, audience),
        sections=sections,
    )
    logger.info(
        "tool_call",
        tool="review_draft",
        audience=audience,
        content_type=content_type,
        text_chars=len(text),
        sections=[s.name for s in sections],
    )
    return brief
