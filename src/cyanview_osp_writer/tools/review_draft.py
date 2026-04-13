"""review_draft orchestrator — runs all six layers and returns a ReviewBrief."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.check_audience import check_audience
from cyanview_osp_writer.tools.check_claims import check_claims
from cyanview_osp_writer.tools.check_glossary import check_glossary
from cyanview_osp_writer.tools.models import ReviewBrief, ReviewSection
from cyanview_osp_writer.tools.osp_edit import osp_edit
from cyanview_osp_writer.tools.osp_meta import osp_meta
from cyanview_osp_writer.tools.osp_seo import osp_seo

logger = structlog.get_logger(__name__)

VALID_AUDIENCES = {"dp", "broadcast_engineer", "rental_house", "mixed"}
VALID_CONTENT_TYPES = {
    "landing_page",
    "blog_post",
    "product_brief",
    "release_note",
    "other",
}
VALID_FOCUS = (
    "glossary",
    "claims",
    "audience",
    "osp_edit",
    "osp_seo",
    "osp_meta",
)
MAX_TEXT_CHARS = 50_000


def _build_execution_plan(active: list[str], audience: str) -> list[str]:
    plan: list[str] = [
        "1. Read the structured sections below as your marching orders.",
        f"2. Render the review for audience={audience}.",
    ]
    step = 3
    if "glossary" in active:
        plan.append(
            f"{step}. Apply glossary hits inline: show each rejected term "
            "with its canonical replacement."
        )
        step += 1
    if "claims" in active:
        plan.append(
            f"{step}. Apply claims hits: rewrite each high-severity "
            "superlative or unsourced technical claim."
        )
        step += 1
    if "audience" in active:
        plan.append(
            f"{step}. Apply audience guidance: flag tone mismatches and "
            "assumed-knowledge gaps for the named audience."
        )
        step += 1
    if "osp_edit" in active:
        plan.append(
            f"{step}. Apply OSP Editing Codes: produce a code-tagged "
            "review with before/after suggestions."
        )
        step += 1
    if "osp_seo" in active:
        plan.append(
            f"{step}. Apply OSP On-Page SEO: suggest keyword integration "
            "and structure improvements."
        )
        step += 1
    if "osp_meta" in active:
        plan.append(
            f"{step}. Apply OSP Meta guide: produce H1, meta title "
            "(50-60), meta description (155-160), slug."
        )
        step += 1
    plan.append(
        f"{step}. Summarise the top 3 most-impactful changes at the end."
    )
    return plan


def review_draft(
    text: str,
    audience: str,
    content_type: str,
    focus: list[str] | None = None,
) -> ReviewBrief:
    """Run all six review layers and return a structured ReviewBrief."""
    if audience not in VALID_AUDIENCES:
        raise ValueError(
            f"invalid_audience: {audience!r}; must be one of "
            f"{sorted(VALID_AUDIENCES)}"
        )
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(
            f"invalid_content_type: {content_type!r}; must be one of "
            f"{sorted(VALID_CONTENT_TYPES)}"
        )
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call review_draft per section."
        )
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
