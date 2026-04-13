"""MCP server bootstrap for cyanview-osp-writer."""

from __future__ import annotations

import structlog
from mcp.server.fastmcp import FastMCP

from cyanview_osp_writer.resources import load_resources

logger = structlog.get_logger(__name__)


def build_server() -> FastMCP:
    """Construct and return the configured MCP server.

    Loads bundled resources eagerly so any validation failure
    surfaces at startup, not at first tool call.
    """
    resources = load_resources()
    logger.info(
        "resources_loaded",
        glossary_terms=len(resources.glossary.terms),
        audiences=list(resources.audiences.audiences.keys()),
        banned_superlatives=len(resources.claims.banned_superlatives),
        osp_source_sha=resources.osp_source_sha,
    )

    server = FastMCP("cyanview-osp-writer")

    # Tools registered in subsequent tasks via register_tools(server, resources).
    return server


def run() -> None:
    server = build_server()
    server.run()
