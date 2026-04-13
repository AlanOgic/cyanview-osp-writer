"""Claims regex layer — deterministic detection of banned/unsourced claims."""

from dataclasses import dataclass
from typing import Literal

import regex

from cyanview_osp_writer.schemas import ClaimPattern, ClaimsFile

REGEX_TIMEOUT_SECONDS = 0.1

ClaimCategory = Literal["banned_superlative", "technical_claim"]
Severity = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class ClaimsHit:
    matched_text: str
    start: int
    end: int
    category: ClaimCategory
    severity: Severity
    reason: str


@dataclass(frozen=True)
class _CompiledPattern:
    pattern: regex.Pattern[str]
    category: ClaimCategory
    severity: Severity
    reason: str


class ClaimsEngine:
    def __init__(self, claims: ClaimsFile) -> None:
        self._patterns: list[_CompiledPattern] = []
        for c in claims.banned_superlatives:
            self._patterns.append(self._compile(c, "banned_superlative"))
        for c in claims.technical_claims_needing_source:
            self._patterns.append(self._compile(c, "technical_claim"))
        self._require_sourcing_topics: list[str] = list(claims.require_sourcing_topics)

    @property
    def require_sourcing_topics(self) -> list[str]:
        return list(self._require_sourcing_topics)

    @staticmethod
    def _compile(c: ClaimPattern, category: ClaimCategory) -> _CompiledPattern:
        return _CompiledPattern(
            pattern=regex.compile(c.pattern, flags=regex.IGNORECASE),
            category=category,
            severity=c.severity,
            reason=c.reason,
        )

    def scan(self, text: str) -> list[ClaimsHit]:
        """Scan text for banned/unsourced claims; return hits sorted by offset.

        Unlike the glossary layer, claims are scanned everywhere in the text
        with no code-block masking.

        Raises:
            TimeoutError: If a compiled pattern exceeds
                ``REGEX_TIMEOUT_SECONDS`` on the input. Callers that accept
                untrusted claims YAML should wrap this call and surface
                the timeout as a structured error.
        """
        hits: list[ClaimsHit] = []
        for cp in self._patterns:
            for m in cp.pattern.finditer(text, timeout=REGEX_TIMEOUT_SECONDS):
                hits.append(
                    ClaimsHit(
                        matched_text=text[m.start() : m.end()],
                        start=m.start(),
                        end=m.end(),
                        category=cp.category,
                        severity=cp.severity,
                        reason=cp.reason,
                    )
                )
        hits.sort(key=lambda h: h.start)
        return hits
