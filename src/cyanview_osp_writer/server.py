"""MCP server bootstrap for cyanview-osp-writer."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable

import structlog
from mcp.server.fastmcp import FastMCP

from cyanview_osp_writer.resources import load_resources


def _configure_logging() -> None:
    """Wire stdlib logging + structlog to stderr-only JSON.

    Called once from :func:`run`; intentionally NOT invoked at import time so
    that test code paths exercising :func:`build_server` don't mutate global
    logging configuration.
    """
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

    from cyanview_osp_writer.tools.osp_writing import osp_writing

    @server.tool()
    def osp_writing_tool(text: str) -> dict:
        """Return OSP Writing Guide guidance plus the draft."""
        return osp_writing(text).model_dump()

    from cyanview_osp_writer.tools.osp_value_map import osp_value_map

    @server.tool()
    def osp_value_map_tool(text: str) -> dict:
        """Return OSP Value Map guidance plus the draft."""
        return osp_value_map(text).model_dump()

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

    from importlib import resources as ir

    def _read_cyanview(filename: str) -> str:
        return (
            ir.files("cyanview_osp_writer")
            .joinpath("resources")
            .joinpath("cyanview")
            .joinpath(filename)
            .read_text(encoding="utf-8")
        )

    @server.resource("cyanview://glossary.yaml")
    def _glossary_resource() -> str:
        return _read_cyanview("glossary.yaml")

    @server.resource("cyanview://audiences.yaml")
    def _audiences_resource() -> str:
        return _read_cyanview("audiences.yaml")

    @server.resource("cyanview://claims-patterns.yaml")
    def _claims_resource() -> str:
        return _read_cyanview("claims-patterns.yaml")

    def _make_osp_resource(guide_name: str) -> Callable[[], str]:
        @server.resource(f"osp://{guide_name}.md")
        def _osp_resource() -> str:
            return resources.osp_guides[guide_name]

        return _osp_resource

    _osp_guide_names = (
        "writing-guide",
        "editing-codes",
        "seo-guide",
        "meta-guide",
        "value-map",
    )
    for _guide in _osp_guide_names:
        _make_osp_resource(_guide)

    return server


def run() -> None:
    _configure_logging()
    server = build_server()
    server.run()
