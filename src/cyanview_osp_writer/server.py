"""MCP server bootstrap for cyanview-osp-writer."""

from __future__ import annotations

import logging
import sys

import structlog
from mcp.server.fastmcp import FastMCP

from cyanview_osp_writer.resources import load_resources


def _configure_logging() -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=logging.INFO,
    )
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


_configure_logging()
logger = structlog.get_logger(__name__)


def build_server() -> FastMCP:
    """Construct and return the configured MCP server."""
    resources = load_resources()
    logger.info(
        "resources_loaded",
        glossary_terms=len(resources.glossary.terms),
        audiences=list(resources.audiences.audiences.keys()),
        banned_superlatives=len(resources.claims.banned_superlatives),
        osp_source_sha=resources.osp_source_sha,
    )

    server = FastMCP("cyanview-osp-writer")

    from cyanview_osp_writer.tools.check_glossary import check_glossary

    @server.tool()
    def check_glossary_tool(text: str) -> dict:
        """Run the Cyanview glossary regex layer and return structured hits."""
        return check_glossary(text).model_dump()

    from cyanview_osp_writer.tools.check_claims import check_claims

    @server.tool()
    def check_claims_tool(text: str) -> dict:
        """Run the Cyanview claims regex layer and return structured hits."""
        return check_claims(text).model_dump()

    from cyanview_osp_writer.tools.check_audience import check_audience

    @server.tool()
    def check_audience_tool(text: str, audience: str) -> dict:
        """Assemble an audience-tone review prompt for the host LLM."""
        return check_audience(text, audience).model_dump()

    from cyanview_osp_writer.tools.osp_edit import osp_edit

    @server.tool()
    def osp_edit_tool(text: str) -> dict:
        """Return OSP Editing Codes guidance plus the draft."""
        return osp_edit(text).model_dump()

    from cyanview_osp_writer.tools.osp_seo import osp_seo

    @server.tool()
    def osp_seo_tool(text: str, target_keywords: list[str] | None = None) -> dict:
        """Return OSP On-Page SEO guidance plus the draft."""
        return osp_seo(text, target_keywords).model_dump()

    from cyanview_osp_writer.tools.osp_meta import osp_meta

    @server.tool()
    def osp_meta_tool(text: str) -> dict:
        """Return OSP Meta-information guidance plus the draft."""
        return osp_meta(text).model_dump()

    from cyanview_osp_writer.tools.review_draft import review_draft

    @server.tool()
    def review_draft_tool(
        text: str,
        audience: str,
        content_type: str,
        focus: list[str] | None = None,
    ) -> dict:
        """Run the full review pipeline and return a structured ReviewBrief."""
        return review_draft(text, audience, content_type, focus).model_dump()

    return server


def run() -> None:
    server = build_server()
    server.run()
