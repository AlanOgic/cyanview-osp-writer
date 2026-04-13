"""Glossary regex layer — deterministic detection of rejected terms."""

from dataclasses import dataclass

import regex

from cyanview_osp_writer.schemas import GlossaryFile, GlossaryTerm

REGEX_TIMEOUT_SECONDS = 0.1

# Match fenced code blocks (```...```) and inline code (`...`).
_CODE_BLOCK_PATTERN = regex.compile(
    r"```.*?```|`[^`\n]*`",
    flags=regex.DOTALL,
)


@dataclass(frozen=True)
class GlossaryHit:
    canonical: str
    matched_text: str
    start: int
    end: int
    note: str | None


@dataclass(frozen=True)
class _CompiledTerm:
    canonical: str
    note: str | None
    case_sensitive_pattern: regex.Pattern[str] | None
    case_insensitive_pattern: regex.Pattern[str] | None


class GlossaryEngine:
    def __init__(self, glossary: GlossaryFile) -> None:
        self._terms: list[_CompiledTerm] = [
            self._compile(t) for t in glossary.terms
        ]

    @staticmethod
    def _compile(term: GlossaryTerm) -> _CompiledTerm:
        rejects = list(term.reject) + list(term.deprecated_aliases)
        if not rejects:
            return _CompiledTerm(
                canonical=term.canonical,
                note=term.note,
                case_sensitive_pattern=None,
                case_insensitive_pattern=None,
            )
        # Split into case-sensitive (those that share a case-insensitive form
        # with an accepted variant) and case-insensitive (the rest).
        accepted_lower = {a.lower() for a in term.accept}
        case_sensitive: list[str] = []
        case_insensitive: list[str] = []
        for r in rejects:
            if r.lower() in accepted_lower:
                case_sensitive.append(r)
            else:
                case_insensitive.append(r)

        def _build(parts: list[str], flags: int) -> regex.Pattern[str] | None:
            if not parts:
                return None
            alternation = "|".join(regex.escape(p) for p in parts)
            return regex.compile(rf"\b(?:{alternation})\b", flags=flags)

        return _CompiledTerm(
            canonical=term.canonical,
            note=term.note,
            case_sensitive_pattern=_build(case_sensitive, 0),
            case_insensitive_pattern=_build(case_insensitive, regex.IGNORECASE),
        )

    def scan(self, text: str) -> list[GlossaryHit]:
        """Scan text for rejected glossary terms; return hits sorted by offset.

        Raises:
            TimeoutError: If a compiled pattern exceeds
                ``REGEX_TIMEOUT_SECONDS`` on the input. Callers that accept
                untrusted glossary YAML should wrap this call and surface
                the timeout as a structured error.
        """
        masked = self._mask_code_blocks(text)
        hits: list[GlossaryHit] = []
        for term in self._terms:
            for pattern in (term.case_sensitive_pattern, term.case_insensitive_pattern):
                if pattern is None:
                    continue
                for m in pattern.finditer(masked, timeout=REGEX_TIMEOUT_SECONDS):
                    hits.append(
                        GlossaryHit(
                            canonical=term.canonical,
                            matched_text=text[m.start() : m.end()],
                            start=m.start(),
                            end=m.end(),
                            note=term.note,
                        )
                    )
        hits.sort(key=lambda h: h.start)
        return hits

    @staticmethod
    def _mask_code_blocks(text: str) -> str:
        """Replace code-block content with spaces so regex offsets stay aligned."""

        def _blank(m: regex.Match[str]) -> str:
            return " " * (m.end() - m.start())

        return _CODE_BLOCK_PATTERN.sub(_blank, text)
