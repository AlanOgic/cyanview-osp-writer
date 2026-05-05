"""Shared constants used by tools, schemas, and the orchestrator.

Single-source for the audience taxonomy, content types, focus subset, and
text-size cap. The v0.2.0 audience refactor changes only this file plus
``resources/cyanview/audiences.yaml`` and the audience tests.
"""

from __future__ import annotations

# Audience keys present in resources/cyanview/audiences.yaml.
BASE_AUDIENCES: frozenset[str] = frozenset(
    {"dp", "broadcast_engineer", "rental_house"}
)

# Audience values accepted by tools — the base set plus "mixed", which means
# "review against all three profiles and call out conflicts".
VALID_AUDIENCES: frozenset[str] = BASE_AUDIENCES | {"mixed"}

# Content types accepted by review_draft.
VALID_CONTENT_TYPES: frozenset[str] = frozenset(
    {
        "landing_page",
        "blog_post",
        "product_brief",
        "release_note",
        "other",
    }
)

# Focus subset names accepted by review_draft. Order is significant —
# section ordering in ReviewBrief follows this tuple.
VALID_FOCUS: tuple[str, ...] = (
    "glossary",
    "claims",
    "audience",
    "osp_edit",
    "osp_seo",
    "osp_meta",
)

# Per-tool input cap. Drafts longer than this must be split by the caller.
MAX_TEXT_CHARS: int = 50_000
