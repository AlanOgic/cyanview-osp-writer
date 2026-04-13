"""Pydantic output models shared by tools."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class GlossaryHitOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical: str
    matched_text: str
    start: int
    end: int
    note: str | None = None


class GlossaryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hits: list[GlossaryHitOut]
    summary: str


class ClaimsHitOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    matched_text: str
    start: int
    end: int
    category: Literal["banned_superlative", "technical_claim"]
    severity: Literal["low", "medium", "high"]
    reason: str


class ClaimsResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hits: list[ClaimsHitOut]
    require_sourcing_topics: list[str]
    summary: str


class GuidanceResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guidance: str
    draft: str
    source: str  # e.g. "osp:editing-codes", "cyanview:audience:dp"


class ReviewSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    payload: dict[str, Any]


class ReviewBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audience: str
    content_type: str
    osp_source_sha: str
    execution_plan: list[str]
    sections: list[ReviewSection] = Field(default_factory=list)
