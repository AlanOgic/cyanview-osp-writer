"""Shared input validation for tool entry points.

Each helper raises ``ValueError`` with a structured, parseable message of the
form ``<reason>: <detail>`` so MCP clients can branch on the reason.
"""

from __future__ import annotations

from cyanview_osp_writer._constants import MAX_TEXT_CHARS, VALID_AUDIENCES


def validate_text(text: str, tool_name: str) -> None:
    """Raise ``ValueError`` if ``text`` exceeds :data:`MAX_TEXT_CHARS`."""
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            f"split into sections and call {tool_name} per section."
        )


def validate_audience(audience: str) -> None:
    """Raise ``ValueError`` if ``audience`` is not in :data:`VALID_AUDIENCES`."""
    if audience not in VALID_AUDIENCES:
        raise ValueError(
            f"invalid_audience: {audience!r}; must be one of "
            f"{sorted(VALID_AUDIENCES)}"
        )
