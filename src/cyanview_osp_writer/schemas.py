"""Pydantic schemas validating bundled YAML resource files."""

from typing import Literal

import regex
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class GlossaryTerm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    canonical: str
    full_name: str | None = None
    accept: list[str] = Field(default_factory=list)
    reject: list[str] = Field(default_factory=list)
    deprecated_aliases: list[str] = Field(default_factory=list)
    note: str | None = None


class GlossaryFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    terms: list[GlossaryTerm]


class AudienceProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    assumes: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    tone: str


REQUIRED_AUDIENCES = {"dp", "broadcast_engineer", "rental_house"}


class AudiencesFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    audiences: dict[str, AudienceProfile]

    @model_validator(mode="after")
    def _require_three(self) -> "AudiencesFile":
        missing = REQUIRED_AUDIENCES - set(self.audiences.keys())
        if missing:
            raise ValueError(f"Missing required audiences: {sorted(missing)}")
        return self


class ClaimPattern(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pattern: str
    severity: Literal["low", "medium", "high"]
    reason: str

    @field_validator("pattern")
    @classmethod
    def _compilable(cls, v: str) -> str:
        try:
            regex.compile(v)
        except regex.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc
        return v


class ClaimsFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    banned_superlatives: list[ClaimPattern] = Field(default_factory=list)
    technical_claims_needing_source: list[ClaimPattern] = Field(default_factory=list)
    require_sourcing_topics: list[str] = Field(default_factory=list)
