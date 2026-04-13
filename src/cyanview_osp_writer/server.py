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

    return server


def run() -> None:
    server = build_server()
    server.run()
