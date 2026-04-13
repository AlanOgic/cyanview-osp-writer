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
    return server


def run() -> None:
    server = build_server()
    server.run()
