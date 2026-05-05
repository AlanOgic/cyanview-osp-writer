"""Audience prompt-assembly layer."""

from dataclasses import dataclass
from typing import Literal

from cyanview_osp_writer.schemas import AudienceProfile, AudiencesFile

AudienceKey = Literal["dp", "broadcast_engineer", "rental_house", "mixed"]


@dataclass(frozen=True)
class AudienceReview:
    audience: str
    profiles: list[AudienceProfile]
    draft: str
    guidance: str


_INSTRUCTIONS_SINGLE = """\
Review the draft below for tone, vocabulary, and assumed-knowledge fit
against the {label} audience profile. Flag passages that:
- Violate the tone: {tone}
- Use language listed under "avoid"
- Assume knowledge the audience does not have
- Fail to assume knowledge the audience already has

Profile:
- Label: {label}
- Assumes: {assumes}
- Avoid: {avoid}
- Tone: {tone}
"""

_INSTRUCTIONS_MIXED = """\
Review the draft below against ALL THREE Cyanview audience profiles below.
Note where the draft serves one audience well but fails another. When the
audiences have conflicting needs (e.g., DP vs broadcast engineer), call
out the conflict explicitly rather than picking a side.

{profiles}
"""


class AudienceLayer:
    def __init__(self, audiences: AudiencesFile) -> None:
        self._audiences = audiences

    def assemble(self, draft: str, audience: AudienceKey | str) -> AudienceReview:
        if audience == "mixed":
            profiles = [
                self._audiences.audiences["dp"],
                self._audiences.audiences["broadcast_engineer"],
                self._audiences.audiences["rental_house"],
            ]
            guidance = _INSTRUCTIONS_MIXED.format(
                profiles="\n".join(self._format_profile(p) for p in profiles),
            )
        else:
            profile = self._audiences.audiences[audience]
            profiles = [profile]
            guidance = _INSTRUCTIONS_SINGLE.format(
                label=profile.label,
                tone=profile.tone,
                assumes=", ".join(profile.assumes) or "(none)",
                avoid=", ".join(profile.avoid) or "(none)",
            )
        return AudienceReview(
            audience=audience,
            profiles=profiles,
            draft=draft,
            guidance=guidance,
        )

    @staticmethod
    def _format_profile(p: AudienceProfile) -> str:
        return (
            f"- Label: {p.label}\n"
            f"  Assumes: {', '.join(p.assumes) or '(none)'}\n"
            f"  Avoid:   {', '.join(p.avoid) or '(none)'}\n"
            f"  Tone:    {p.tone}\n"
        )
