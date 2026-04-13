"""Bundled resource loader. Validates and caches all YAML/MD resources."""

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources as importlib_resources

import yaml

from cyanview_osp_writer.schemas import (
    AudiencesFile,
    ClaimsFile,
    GlossaryFile,
)

OSP_GUIDE_NAMES = (
    "writing-guide",
    "editing-codes",
    "seo-guide",
    "meta-guide",
    "value-map",
)


@dataclass(frozen=True)
class Resources:
    glossary: GlossaryFile
    audiences: AudiencesFile
    claims: ClaimsFile
    osp_guides: dict[str, str]
    osp_source_sha: str


def _read_text(*parts: str) -> str:
    files = importlib_resources.files("cyanview_osp_writer.resources")
    for p in parts:
        files = files.joinpath(p)
    return files.read_text(encoding="utf-8")


def _load_yaml(filename: str) -> dict:
    return yaml.safe_load(_read_text("cyanview", filename))


@lru_cache(maxsize=1)
def load_resources() -> Resources:
    glossary = GlossaryFile.model_validate(_load_yaml("glossary.yaml"))
    audiences = AudiencesFile.model_validate(_load_yaml("audiences.yaml"))
    claims = ClaimsFile.model_validate(_load_yaml("claims-patterns.yaml"))

    osp_guides: dict[str, str] = {}
    for name in OSP_GUIDE_NAMES:
        osp_guides[name] = _read_text("osp", f"{name}.md")

    try:
        osp_source_sha = _read_text("osp", ".source-sha").strip()
    except FileNotFoundError:
        osp_source_sha = "unknown"

    return Resources(
        glossary=glossary,
        audiences=audiences,
        claims=claims,
        osp_guides=osp_guides,
        osp_source_sha=osp_source_sha,
    )


def reset_cache() -> None:
    """Test helper — clears the lru_cache so subsequent calls re-read."""
    load_resources.cache_clear()
