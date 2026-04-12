# cyanview-osp-writer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local stdio MCP server in Python that reviews Cyanview marketing/documentation drafts using Open Strategy Partners (OSP) methodology bundled as MCP resources, layered with three Cyanview-specific brand checks (glossary, audience tone, unverifiable claims).

**Architecture:** Single Python package (`cyanview_osp_writer`) exposing one orchestrator MCP tool (`review_draft`) and six sub-tools. OSP guidance is bundled as static markdown resources (synced from upstream via a script + weekly CI). Cyanview brand layers are YAML resources with deterministic regex engines for glossary/claims and prompt-assembly for audience. Tools return structured prompts and data; the host LLM does the actual review work.

**Tech Stack:** Python 3.11+, `mcp>=1.0` SDK, `pydantic>=2.0`, `pyyaml>=6.0`, `structlog>=24.0`, `regex>=2024.0`, `uv` for tooling, `pytest` + `pytest-asyncio` + `pytest-cov` for tests, `hatch` build backend, GitHub Actions CI.

**Spec:** `docs/superpowers/specs/2026-04-12-cyanview-osp-writer-design.md`

**Repo (planned):** `alanogic/cyanview-osp-writer`

---

## File Structure

Created or modified by this plan:

```
osp-writer/
├── pyproject.toml                                      # Task 1
├── README.md                                            # Task 24
├── LICENSE                                              # Task 1
├── ATTRIBUTION.md                                       # Task 1
├── .github/workflows/test.yml                           # Task 22
├── .github/workflows/sync-osp.yml                       # Task 23
├── .gitignore                                           # Task 1
├── scripts/sync_osp.py                                  # Task 23
├── src/cyanview_osp_writer/
│   ├── __init__.py                                      # Task 1
│   ├── __main__.py                                      # Task 12
│   ├── server.py                                        # Task 12
│   ├── resources.py                                     # Task 7
│   ├── schemas.py                                       # Task 2
│   ├── tools/
│   │   ├── __init__.py                                  # Task 13
│   │   ├── check_glossary.py                            # Task 13
│   │   ├── check_claims.py                              # Task 14
│   │   ├── check_audience.py                            # Task 15
│   │   ├── osp_edit.py                                  # Task 16
│   │   ├── osp_seo.py                                   # Task 17
│   │   ├── osp_meta.py                                  # Task 18
│   │   └── review_draft.py                              # Task 19
│   ├── layers/
│   │   ├── __init__.py                                  # Task 4
│   │   ├── glossary.py                                  # Task 4
│   │   ├── claims.py                                    # Task 5
│   │   └── audience.py                                  # Task 6
│   └── resources/
│       ├── osp/
│       │   ├── writing-guide.md                         # Task 9 (placeholder), Task 23 (sync)
│       │   ├── editing-codes.md                         # Task 9
│       │   ├── seo-guide.md                             # Task 9
│       │   ├── meta-guide.md                            # Task 9
│       │   ├── value-map.md                             # Task 9
│       │   ├── ATTRIBUTION.md                           # Task 9
│       │   └── .source-sha                              # Task 9
│       └── cyanview/
│           ├── glossary.yaml                            # Task 3
│           ├── audiences.yaml                           # Task 3
│           └── claims-patterns.yaml                     # Task 3
└── tests/
    ├── conftest.py                                      # Task 1
    ├── fixtures/
    │   ├── drafts/
    │   │   ├── clean.md                                 # Task 4
    │   │   ├── glossary_violations.md                   # Task 4
    │   │   ├── claims_violations.md                     # Task 5
    │   │   ├── mixed_violations.md                      # Task 19
    │   │   └── with_code_blocks.md                      # Task 4
    │   └── osp_snapshot/                                # Task 23
    ├── test_schemas.py                                  # Task 2
    ├── test_resources.py                                # Task 7
    ├── layers/
    │   ├── test_glossary.py                             # Task 4
    │   ├── test_claims.py                               # Task 5
    │   └── test_audience.py                             # Task 6
    ├── tools/
    │   ├── test_check_glossary.py                       # Task 13
    │   ├── test_check_claims.py                         # Task 14
    │   ├── test_check_audience.py                       # Task 15
    │   ├── test_osp_edit.py                             # Task 16
    │   ├── test_osp_seo.py                              # Task 17
    │   ├── test_osp_meta.py                             # Task 18
    │   └── test_review_draft.py                         # Task 19
    └── integration/
        ├── test_server_startup.py                       # Task 20
        ├── test_resource_validation.py                  # Task 21
        └── test_sync_script.py                          # Task 23
```

Each tool, layer, and schema lives in its own file. Files stay in the 50-300 line range per the spec.

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `LICENSE`
- Create: `ATTRIBUTION.md`
- Create: `.gitignore`
- Create: `src/cyanview_osp_writer/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "cyanview-osp-writer"
version = "0.1.0"
description = "MCP server reviewing Cyanview drafts with OSP methodology + Cyanview brand layers"
requires-python = ">=3.11"
license = { text = "CC-BY-SA-4.0" }
authors = [{ name = "alanogic" }]
dependencies = [
  "mcp>=1.0",
  "pydantic>=2.0",
  "pyyaml>=6.0",
  "structlog>=24.0",
  "regex>=2024.0",
]

[project.scripts]
cyanview-osp-writer = "cyanview_osp_writer.__main__:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/cyanview_osp_writer"]

[tool.hatch.build.targets.wheel.force-include]
"src/cyanview_osp_writer/resources" = "cyanview_osp_writer/resources"

[dependency-groups]
dev = [
  "pytest>=8.0",
  "pytest-asyncio>=0.23",
  "pytest-cov>=5.0",
  "ruff>=0.6",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.coverage.run]
source = ["src/cyanview_osp_writer"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
```

- [ ] **Step 2: Create `LICENSE`** (CC BY-SA 4.0 — full text from https://creativecommons.org/licenses/by-sa/4.0/legalcode.txt). Save the canonical CC BY-SA 4.0 legalcode text into this file verbatim.

- [ ] **Step 3: Create `ATTRIBUTION.md`**

```markdown
# Attribution

`cyanview-osp-writer` bundles methodology guidance derived from:

> **Open Strategy Partners — `osp_marketing_tools`**
> https://github.com/open-strategy-partners/osp_marketing_tools
> Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
> https://creativecommons.org/licenses/by-sa/4.0/

Per CC BY-SA 4.0, this project distributes modified and unmodified excerpts of OSP materials under the same license. The synced commit SHA is recorded in `src/cyanview_osp_writer/resources/osp/.source-sha`.

Cyanview-specific brand layer content (`src/cyanview_osp_writer/resources/cyanview/*`) is also released under CC BY-SA 4.0.
```

- [ ] **Step 4: Create `.gitignore`**

```
__pycache__/
*.pyc
*.pyo
.venv/
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.ruff_cache/
/tmp/
```

- [ ] **Step 5: Create `src/cyanview_osp_writer/__init__.py`**

```python
"""cyanview-osp-writer — MCP server for Cyanview draft review with OSP methodology."""

__version__ = "0.1.0"
```

- [ ] **Step 6: Create `tests/conftest.py`**

```python
"""Shared pytest fixtures."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def draft_clean(fixtures_dir: Path) -> str:
    return (fixtures_dir / "drafts" / "clean.md").read_text(encoding="utf-8")
```

- [ ] **Step 7: Initialize uv environment and verify**

Run:
```bash
cd /Users/alanogic/cdev/osp-writer
uv sync
uv run python -c "import cyanview_osp_writer; print(cyanview_osp_writer.__version__)"
```

Expected: prints `0.1.0`. No errors.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml LICENSE ATTRIBUTION.md .gitignore src/cyanview_osp_writer/__init__.py tests/conftest.py uv.lock
git commit -m "chore: scaffold cyanview-osp-writer package"
```

---

## Task 2: Pydantic Schemas for YAML Resources

**Files:**
- Create: `src/cyanview_osp_writer/schemas.py`
- Test: `tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_schemas.py`:

```python
"""Tests for pydantic schemas validating bundled YAML resources."""

import pytest
from pydantic import ValidationError

from cyanview_osp_writer.schemas import (
    AudienceProfile,
    AudiencesFile,
    ClaimPattern,
    ClaimsFile,
    GlossaryFile,
    GlossaryTerm,
)


class TestGlossaryTerm:
    def test_minimal_term_valid(self):
        term = GlossaryTerm(canonical="RCP", reject=["remote panel"])
        assert term.canonical == "RCP"
        assert term.reject == ["remote panel"]
        assert term.accept == []
        assert term.deprecated_aliases == []
        assert term.note is None

    def test_full_term_valid(self):
        term = GlossaryTerm(
            canonical="RIO Live",
            full_name="RIO Live system",
            accept=["RIO Live", "RIO-Live"],
            reject=["RioLive"],
            deprecated_aliases=["Rio"],
            note="Always capitalize",
        )
        assert term.full_name == "RIO Live system"

    def test_canonical_required(self):
        with pytest.raises(ValidationError):
            GlossaryTerm(reject=["x"])


class TestGlossaryFile:
    def test_valid(self):
        f = GlossaryFile(version=1, terms=[GlossaryTerm(canonical="RCP")])
        assert f.version == 1
        assert len(f.terms) == 1

    def test_version_must_be_one(self):
        with pytest.raises(ValidationError):
            GlossaryFile(version=2, terms=[])


class TestAudienceProfile:
    def test_valid(self):
        p = AudienceProfile(
            label="DP",
            assumes=["cinematic language"],
            avoid=["jargon"],
            tone="creative",
        )
        assert p.label == "DP"


class TestAudiencesFile:
    def test_three_required_audiences(self):
        f = AudiencesFile(
            version=1,
            audiences={
                "dp": AudienceProfile(label="DP", assumes=[], avoid=[], tone="x"),
                "broadcast_engineer": AudienceProfile(
                    label="BE", assumes=[], avoid=[], tone="x"
                ),
                "rental_house": AudienceProfile(
                    label="RH", assumes=[], avoid=[], tone="x"
                ),
            },
        )
        assert set(f.audiences.keys()) == {"dp", "broadcast_engineer", "rental_house"}

    def test_missing_audience_rejected(self):
        with pytest.raises(ValidationError):
            AudiencesFile(
                version=1,
                audiences={
                    "dp": AudienceProfile(label="DP", assumes=[], avoid=[], tone="x")
                },
            )


class TestClaimPattern:
    def test_valid(self):
        c = ClaimPattern(
            pattern=r"\bindustry-leading\b", severity="high", reason="vague"
        )
        assert c.severity == "high"

    def test_invalid_regex_rejected(self):
        with pytest.raises(ValidationError):
            ClaimPattern(pattern="[unclosed", severity="high", reason="bad")

    def test_severity_enum(self):
        with pytest.raises(ValidationError):
            ClaimPattern(pattern="x", severity="critical", reason="r")


class TestClaimsFile:
    def test_valid(self):
        f = ClaimsFile(
            version=1,
            banned_superlatives=[
                ClaimPattern(pattern="x", severity="high", reason="r")
            ],
            technical_claims_needing_source=[],
            require_sourcing_topics=["latency"],
        )
        assert len(f.banned_superlatives) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_schemas.py -v`
Expected: FAIL — `ModuleNotFoundError: cyanview_osp_writer.schemas`

- [ ] **Step 3: Implement `src/cyanview_osp_writer/schemas.py`**

```python
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
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_schemas.py -v`
Expected: PASS, all 11 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/cyanview_osp_writer/schemas.py tests/test_schemas.py
git commit -m "feat: add pydantic schemas for bundled YAML resources"
```

---

## Task 3: Seed Cyanview YAML Resources

**Files:**
- Create: `src/cyanview_osp_writer/resources/cyanview/glossary.yaml`
- Create: `src/cyanview_osp_writer/resources/cyanview/audiences.yaml`
- Create: `src/cyanview_osp_writer/resources/cyanview/claims-patterns.yaml`

These are seed files. They're real data, validated by the schemas from Task 2. The user will expand the glossary later — start with a defensible minimum that the test suite can lock in.

- [ ] **Step 1: Create `glossary.yaml` (seed: 5 terms)**

```yaml
version: 1
terms:
  - canonical: "RCP"
    full_name: "Remote Control Panel"
    accept: ["RCP", "Remote Control Panel"]
    reject: ["remote panel", "control pad"]
    note: "Spell out on first use in external content."
  - canonical: "RIO Live"
    accept: ["RIO Live", "RIO-Live"]
    reject: ["RioLive", "Rio Live system"]
    note: "Two words, capital R-I-O, capital L."
  - canonical: "camera control"
    accept: ["camera control", "camera control system"]
    reject: ["camera remote", "camera controller software"]
    note: "Cyanview sells camera control systems, not 'remotes'."
  - canonical: "CCU"
    full_name: "Camera Control Unit"
    accept: ["CCU", "Camera Control Unit"]
    reject: []
    note: "Industry-standard term; do not redefine."
  - canonical: "Cyanview"
    accept: ["Cyanview"]
    reject: ["CyanView", "cyanview", "Cyan View", "CYANVIEW"]
    note: "Single word, capital C, lowercase rest."
```

- [ ] **Step 2: Create `audiences.yaml`**

```yaml
version: 1
audiences:
  dp:
    label: "Director of Photography / Cinematographer"
    assumes:
      - "cinematic language"
      - "lens, shutter, ISO, color science fluency"
      - "creative outcomes drive decisions"
    avoid:
      - "deep network protocol jargon"
      - "rack-unit talk"
      - "raw latency numbers without creative context"
    tone: "creative, outcome-focused, visual"
  broadcast_engineer:
    label: "Broadcast / Live Engineer"
    assumes:
      - "SDI/IP workflows"
      - "CCU concepts"
      - "latency budgets and signal integrity"
    avoid:
      - "marketing fluff"
      - "vague seamless or magical claims"
      - "creative-only framing without specs"
    tone: "precise, spec-driven, skeptical of hype"
  rental_house:
    label: "Rental House / Assistant Camera"
    assumes:
      - "gear logistics"
      - "compatibility matrices"
      - "fast turnaround between productions"
    avoid:
      - "abstract workflow talk"
      - "marketing-only framing"
    tone: "practical, checklist-friendly, compatibility-first"
```

- [ ] **Step 3: Create `claims-patterns.yaml`**

```yaml
version: 1
banned_superlatives:
  - pattern: "\\b(industry[- ]leading|first[- ]ever|world['’]?s (best|first)|revolutionary|game[- ]changer|cutting[- ]edge|best[- ]in[- ]class)\\b"
    severity: high
    reason: "Unverifiable marketing superlative — rewrite with concrete evidence."
  - pattern: "\\b(seamless|effortless|magical)\\b"
    severity: medium
    reason: "Vague feel-good adjective — replace with the specific behavior."
technical_claims_needing_source:
  - pattern: "\\bsub[- ]?\\d+\\s?ms\\b"
    severity: medium
    reason: "Latency claim — needs a measurement context or remove."
  - pattern: "\\bzero[- ]latency\\b"
    severity: high
    reason: "Zero-latency is physically impossible — restate as a specific bound."
  - pattern: "\\b(unlimited|100%\\s+(compatible|reliable))\\b"
    severity: high
    reason: "Absolute claim — needs scope qualifier or remove."
require_sourcing_topics:
  - "latency numbers"
  - "compatibility with specific cameras"
  - "throughput / bandwidth figures"
  - "frame-rate or resolution support"
```

- [ ] **Step 4: Verify the YAML parses against the schemas**

Run:
```bash
uv run python -c "
import yaml
from cyanview_osp_writer.schemas import GlossaryFile, AudiencesFile, ClaimsFile
from pathlib import Path
base = Path('src/cyanview_osp_writer/resources/cyanview')
GlossaryFile.model_validate(yaml.safe_load((base / 'glossary.yaml').read_text()))
AudiencesFile.model_validate(yaml.safe_load((base / 'audiences.yaml').read_text()))
ClaimsFile.model_validate(yaml.safe_load((base / 'claims-patterns.yaml').read_text()))
print('all valid')
"
```

Expected: prints `all valid`.

- [ ] **Step 5: Commit**

```bash
git add src/cyanview_osp_writer/resources/cyanview/
git commit -m "feat: seed cyanview glossary, audiences, claims YAML resources"
```

---

## Task 4: Glossary Layer

**Files:**
- Create: `src/cyanview_osp_writer/layers/__init__.py`
- Create: `src/cyanview_osp_writer/layers/glossary.py`
- Create: `tests/layers/__init__.py`
- Create: `tests/layers/test_glossary.py`
- Create: `tests/fixtures/drafts/clean.md`
- Create: `tests/fixtures/drafts/glossary_violations.md`
- Create: `tests/fixtures/drafts/with_code_blocks.md`

- [ ] **Step 1: Create draft fixtures**

`tests/fixtures/drafts/clean.md`:

```markdown
# Cyanview RCP Overview

The Cyanview RCP (Remote Control Panel) is a camera control system designed for broadcast and live production. It supports SDI and IP workflows.
```

`tests/fixtures/drafts/glossary_violations.md`:

```markdown
# CyanView remote panel guide

The CyanView remote panel is a camera remote that pairs with the Rio Live system.
```

`tests/fixtures/drafts/with_code_blocks.md`:

````markdown
# RCP API

Use the RCP API like this:

```python
# remote panel  ← inside code block, should NOT be flagged
client = RemotePanel()
```

But "remote panel" outside the block should be flagged.
````

- [ ] **Step 2: Write the failing test**

Create `tests/layers/__init__.py` (empty file).

Create `tests/layers/test_glossary.py`:

```python
"""Tests for the glossary regex layer."""

from pathlib import Path

import pytest

from cyanview_osp_writer.layers.glossary import GlossaryEngine, GlossaryHit
from cyanview_osp_writer.schemas import GlossaryFile, GlossaryTerm


@pytest.fixture
def engine() -> GlossaryEngine:
    glossary = GlossaryFile(
        version=1,
        terms=[
            GlossaryTerm(
                canonical="RCP",
                accept=["RCP", "Remote Control Panel"],
                reject=["remote panel", "control pad"],
            ),
            GlossaryTerm(
                canonical="Cyanview",
                accept=["Cyanview"],
                reject=["CyanView", "cyanview"],
            ),
            GlossaryTerm(
                canonical="RIO Live",
                accept=["RIO Live"],
                reject=["RioLive", "Rio Live"],
            ),
        ],
    )
    return GlossaryEngine(glossary)


class TestGlossaryEngine:
    def test_clean_draft_no_hits(self, engine: GlossaryEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "clean.md").read_text()
        hits = engine.scan(text)
        assert hits == []

    def test_violations_detected(self, engine: GlossaryEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "glossary_violations.md").read_text()
        hits = engine.scan(text)
        canonicals = {h.canonical for h in hits}
        assert "Cyanview" in canonicals
        assert "RCP" in canonicals
        assert "RIO Live" in canonicals

    def test_hit_includes_offset_and_match(self, engine: GlossaryEngine):
        text = "We sell a remote panel and a control pad."
        hits = engine.scan(text)
        assert len(hits) == 2
        rp = next(h for h in hits if h.matched_text == "remote panel")
        assert rp.canonical == "RCP"
        assert text[rp.start : rp.end] == "remote panel"

    def test_case_insensitive_reject(self, engine: GlossaryEngine):
        hits = engine.scan("REMOTE PANEL")
        assert len(hits) == 1
        assert hits[0].canonical == "RCP"

    def test_case_sensitive_canonical_distinction(self, engine: GlossaryEngine):
        # "CyanView" is rejected, "Cyanview" is accepted — they differ only in case
        hits = engine.scan("CyanView is wrong but Cyanview is fine.")
        assert len(hits) == 1
        assert hits[0].matched_text == "CyanView"

    def test_word_boundary(self, engine: GlossaryEngine):
        # "remote panel" inside a longer non-word context still matches.
        # But "controlpad" (no space) should NOT match "control pad".
        hits = engine.scan("controlpad")
        assert hits == []

    def test_skip_code_blocks(self, engine: GlossaryEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "with_code_blocks.md").read_text()
        hits = engine.scan(text)
        # Only the "remote panel" outside the code block should be flagged.
        assert len(hits) == 1
        assert hits[0].matched_text == "remote panel"
        # And it should be after the code block close.
        assert hits[0].start > text.index("```\n\nBut")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/layers/test_glossary.py -v`
Expected: FAIL — `ModuleNotFoundError: cyanview_osp_writer.layers`.

- [ ] **Step 4: Implement the layer**

Create `src/cyanview_osp_writer/layers/__init__.py` (empty).

Create `src/cyanview_osp_writer/layers/glossary.py`:

```python
"""Glossary regex layer — deterministic detection of rejected terms."""

from dataclasses import dataclass

import regex

from cyanview_osp_writer.schemas import GlossaryFile, GlossaryTerm

REGEX_TIMEOUT_SECONDS = 0.1

# Match fenced code blocks (```...```), inline code (`...`), and indented code blocks.
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
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/layers/test_glossary.py -v`
Expected: PASS, all 7 tests green.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/layers/ tests/layers/ tests/fixtures/drafts/
git commit -m "feat: add glossary regex layer with code-block masking"
```

---

## Task 5: Claims Layer

**Files:**
- Create: `src/cyanview_osp_writer/layers/claims.py`
- Create: `tests/layers/test_claims.py`
- Create: `tests/fixtures/drafts/claims_violations.md`

- [ ] **Step 1: Create fixture**

`tests/fixtures/drafts/claims_violations.md`:

```markdown
# Why Cyanview is industry-leading

Our revolutionary camera control system delivers zero-latency performance and is 100% compatible with every camera ever made. It's seamless and magical.
```

- [ ] **Step 2: Write the failing test**

Create `tests/layers/test_claims.py`:

```python
"""Tests for the claims regex layer."""

from pathlib import Path

import pytest

from cyanview_osp_writer.layers.claims import ClaimsEngine, ClaimsHit
from cyanview_osp_writer.schemas import ClaimPattern, ClaimsFile


@pytest.fixture
def engine() -> ClaimsEngine:
    claims = ClaimsFile(
        version=1,
        banned_superlatives=[
            ClaimPattern(
                pattern=r"\b(industry[- ]leading|revolutionary)\b",
                severity="high",
                reason="vague superlative",
            ),
            ClaimPattern(
                pattern=r"\b(seamless|magical)\b",
                severity="medium",
                reason="feel-good adjective",
            ),
        ],
        technical_claims_needing_source=[
            ClaimPattern(
                pattern=r"\bzero[- ]latency\b",
                severity="high",
                reason="physically impossible",
            ),
            ClaimPattern(
                pattern=r"\b100%\s+compatible\b",
                severity="high",
                reason="absolute claim",
            ),
        ],
        require_sourcing_topics=["latency numbers"],
    )
    return ClaimsEngine(claims)


class TestClaimsEngine:
    def test_clean_draft_no_hits(self, engine: ClaimsEngine, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "clean.md").read_text()
        assert engine.scan(text) == []

    def test_violations_draft_detects_all_categories(
        self, engine: ClaimsEngine, fixtures_dir: Path
    ):
        text = (fixtures_dir / "drafts" / "claims_violations.md").read_text()
        hits = engine.scan(text)
        matched = {h.matched_text.lower() for h in hits}
        assert "industry-leading" in matched
        assert "revolutionary" in matched
        assert "zero-latency" in matched
        assert "100% compatible" in matched
        assert "seamless" in matched
        assert "magical" in matched

    def test_hit_carries_severity_and_category(self, engine: ClaimsEngine):
        hits = engine.scan("This is revolutionary.")
        assert len(hits) == 1
        h = hits[0]
        assert h.severity == "high"
        assert h.category == "banned_superlative"
        assert h.reason == "vague superlative"

    def test_technical_category(self, engine: ClaimsEngine):
        hits = engine.scan("zero latency for everyone")
        assert len(hits) == 1
        assert hits[0].category == "technical_claim"

    def test_offsets_correct(self, engine: ClaimsEngine):
        text = "It is revolutionary technology."
        hits = engine.scan(text)
        assert text[hits[0].start : hits[0].end] == "revolutionary"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/layers/test_claims.py -v`
Expected: FAIL — `ModuleNotFoundError: cyanview_osp_writer.layers.claims`.

- [ ] **Step 4: Implement the layer**

Create `src/cyanview_osp_writer/layers/claims.py`:

```python
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
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/layers/test_claims.py -v`
Expected: PASS, all 5 tests green.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/layers/claims.py tests/layers/test_claims.py tests/fixtures/drafts/claims_violations.md
git commit -m "feat: add claims regex layer for superlatives and unsourced claims"
```

---

## Task 6: Audience Layer

**Files:**
- Create: `src/cyanview_osp_writer/layers/audience.py`
- Create: `tests/layers/test_audience.py`

The audience layer is pure prompt assembly — no LLM, no regex. It returns a structured payload the host LLM uses.

- [ ] **Step 1: Write the failing test**

Create `tests/layers/test_audience.py`:

```python
"""Tests for the audience prompt-assembly layer."""

import pytest

from cyanview_osp_writer.layers.audience import AudienceLayer, AudienceReview
from cyanview_osp_writer.schemas import AudienceProfile, AudiencesFile


@pytest.fixture
def layer() -> AudienceLayer:
    audiences = AudiencesFile(
        version=1,
        audiences={
            "dp": AudienceProfile(
                label="DP", assumes=["cinematic"], avoid=["jargon"], tone="creative"
            ),
            "broadcast_engineer": AudienceProfile(
                label="BE", assumes=["SDI"], avoid=["fluff"], tone="precise"
            ),
            "rental_house": AudienceProfile(
                label="RH", assumes=["logistics"], avoid=["abstract"], tone="practical"
            ),
        },
    )
    return AudienceLayer(audiences)


class TestAudienceLayer:
    def test_single_audience_returns_one_profile(self, layer: AudienceLayer):
        review = layer.assemble("draft text", audience="dp")
        assert isinstance(review, AudienceReview)
        assert len(review.profiles) == 1
        assert review.profiles[0].label == "DP"
        assert review.draft == "draft text"

    def test_mixed_returns_all_three(self, layer: AudienceLayer):
        review = layer.assemble("draft", audience="mixed")
        assert len(review.profiles) == 3
        labels = {p.label for p in review.profiles}
        assert labels == {"DP", "BE", "RH"}

    def test_unknown_audience_raises(self, layer: AudienceLayer):
        with pytest.raises(KeyError):
            layer.assemble("draft", audience="director")

    def test_guidance_includes_tone_and_avoid(self, layer: AudienceLayer):
        review = layer.assemble("draft", audience="broadcast_engineer")
        assert "precise" in review.guidance
        assert "fluff" in review.guidance
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/layers/test_audience.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the layer**

Create `src/cyanview_osp_writer/layers/audience.py`:

```python
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
            guidance = _INSTRUCTIONS_MIXED + "\n" + "\n".join(
                self._format_profile(p) for p in profiles
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
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/layers/test_audience.py -v`
Expected: PASS, all 4 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/cyanview_osp_writer/layers/audience.py tests/layers/test_audience.py
git commit -m "feat: add audience prompt-assembly layer"
```

---

## Task 7: Resources Loader

**Files:**
- Create: `src/cyanview_osp_writer/resources.py`
- Create: `tests/test_resources.py`

This module loads bundled YAML files at startup, validates them with the Task 2 schemas, caches them, and exposes accessor functions. It is the single source of truth for "what the bundled config looks like at runtime."

- [ ] **Step 1: Write the failing test**

Create `tests/test_resources.py`:

```python
"""Tests for the bundled-resources loader."""

import pytest

from cyanview_osp_writer.resources import (
    Resources,
    load_resources,
)
from cyanview_osp_writer.schemas import (
    AudiencesFile,
    ClaimsFile,
    GlossaryFile,
)


class TestLoadResources:
    def test_returns_resources_object(self):
        r = load_resources()
        assert isinstance(r, Resources)

    def test_glossary_parsed(self):
        r = load_resources()
        assert isinstance(r.glossary, GlossaryFile)
        canonicals = {t.canonical for t in r.glossary.terms}
        assert "Cyanview" in canonicals
        assert "RCP" in canonicals

    def test_audiences_parsed_with_three_keys(self):
        r = load_resources()
        assert isinstance(r.audiences, AudiencesFile)
        assert set(r.audiences.audiences.keys()) == {
            "dp",
            "broadcast_engineer",
            "rental_house",
        }

    def test_claims_parsed(self):
        r = load_resources()
        assert isinstance(r.claims, ClaimsFile)
        assert len(r.claims.banned_superlatives) > 0

    def test_osp_guidance_present(self):
        r = load_resources()
        assert "writing-guide" in r.osp_guides
        assert "editing-codes" in r.osp_guides
        assert "seo-guide" in r.osp_guides
        assert "meta-guide" in r.osp_guides
        assert "value-map" in r.osp_guides
        for content in r.osp_guides.values():
            assert isinstance(content, str)
            assert len(content) > 0

    def test_osp_source_sha_present(self):
        r = load_resources()
        assert isinstance(r.osp_source_sha, str)
        assert len(r.osp_source_sha) > 0

    def test_resources_are_cached(self):
        r1 = load_resources()
        r2 = load_resources()
        assert r1 is r2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_resources.py -v`
Expected: FAIL — `ModuleNotFoundError: cyanview_osp_writer.resources`.

- [ ] **Step 3: Implement the loader**

Create `src/cyanview_osp_writer/resources.py`:

```python
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
```

- [ ] **Step 4: Note — tests will fail until Task 9 creates the OSP placeholder files. Move to Task 9 next, then return.**

That's intentional ordering: schemas → cyanview YAML → loader → OSP placeholders → re-run loader tests. Skip running the loader test now; it runs at end of Task 9.

- [ ] **Step 5: Commit**

```bash
git add src/cyanview_osp_writer/resources.py tests/test_resources.py
git commit -m "feat: add bundled resource loader with cached validation"
```

---

## Task 8: OSP Guidance Placeholders

**Files:**
- Create: `src/cyanview_osp_writer/resources/osp/writing-guide.md`
- Create: `src/cyanview_osp_writer/resources/osp/editing-codes.md`
- Create: `src/cyanview_osp_writer/resources/osp/seo-guide.md`
- Create: `src/cyanview_osp_writer/resources/osp/meta-guide.md`
- Create: `src/cyanview_osp_writer/resources/osp/value-map.md`
- Create: `src/cyanview_osp_writer/resources/osp/ATTRIBUTION.md`
- Create: `src/cyanview_osp_writer/resources/osp/.source-sha`

These are placeholders so the loader can run before the sync script (Task 23) replaces them with the real upstream content. Each contains a clearly-marked placeholder header so it's obvious they're not the real thing.

- [ ] **Step 1: Create each guide placeholder**

For each of `writing-guide.md`, `editing-codes.md`, `seo-guide.md`, `meta-guide.md`, `value-map.md`, write:

```markdown
# OSP {NAME} (placeholder)

> This file is a placeholder. Real content is synced from
> https://github.com/open-strategy-partners/osp_marketing_tools
> by `scripts/sync_osp.py`.

Run `uv run python scripts/sync_osp.py` to populate this file.
```

Substitute `{NAME}` with the human-readable guide name (e.g. `Writing Guide`, `Editing Codes`, `SEO Guide`, `Meta Guide`, `Value Map`).

- [ ] **Step 2: Create `ATTRIBUTION.md`**

```markdown
# OSP Source Attribution

Files in this directory (other than this one and `.source-sha`) are derived from:

  https://github.com/open-strategy-partners/osp_marketing_tools

Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).

The synced commit SHA is recorded in `.source-sha`.
```

- [ ] **Step 3: Create `.source-sha`**

```
placeholder
```

(Single line, no trailing prose. The sync script replaces this with the actual upstream commit SHA.)

- [ ] **Step 4: Run the loader test from Task 7**

Run: `uv run pytest tests/test_resources.py -v`
Expected: PASS, all 7 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/cyanview_osp_writer/resources/osp/
git commit -m "feat: add OSP guidance placeholders for sync script"
```

---

## Task 9: Server Bootstrap (no tools yet)

**Files:**
- Create: `src/cyanview_osp_writer/server.py`
- Create: `src/cyanview_osp_writer/__main__.py`

This task wires up the MCP server, registers no tools yet, and validates startup. Tools are added one task at a time after this.

- [ ] **Step 1: Implement `src/cyanview_osp_writer/server.py`**

```python
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
```

- [ ] **Step 2: Implement `src/cyanview_osp_writer/__main__.py`**

```python
"""Console-script entry point."""

from cyanview_osp_writer.server import run


def main() -> None:
    run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verify the server constructs without error**

Run:
```bash
uv run python -c "from cyanview_osp_writer.server import build_server; s = build_server(); print('ok', s.name)"
```
Expected: prints `ok cyanview-osp-writer`.

- [ ] **Step 4: Commit**

```bash
git add src/cyanview_osp_writer/server.py src/cyanview_osp_writer/__main__.py
git commit -m "feat: add MCP server bootstrap with eager resource validation"
```

---

## Task 10: Tool Output Models

**Files:**
- Create: `src/cyanview_osp_writer/tools/__init__.py`
- Create: `src/cyanview_osp_writer/tools/models.py`
- Create: `tests/tools/__init__.py`
- Create: `tests/tools/test_models.py`

Tools share a small set of pydantic output models. Define them once before writing the tools that return them.

- [ ] **Step 1: Write the failing test**

Create `tests/tools/__init__.py` (empty).

Create `tests/tools/test_models.py`:

```python
"""Tests for shared tool output models."""

from cyanview_osp_writer.tools.models import (
    ClaimsHitOut,
    ClaimsResult,
    GlossaryHitOut,
    GlossaryResult,
    GuidanceResult,
    ReviewBrief,
    ReviewSection,
)


class TestModels:
    def test_glossary_hit_out(self):
        h = GlossaryHitOut(
            canonical="RCP", matched_text="remote panel", start=10, end=22, note=None
        )
        assert h.canonical == "RCP"

    def test_glossary_result(self):
        r = GlossaryResult(hits=[], summary="No glossary issues found.")
        assert r.hits == []

    def test_claims_hit_out(self):
        h = ClaimsHitOut(
            matched_text="industry-leading",
            start=0,
            end=16,
            category="banned_superlative",
            severity="high",
            reason="vague",
        )
        assert h.severity == "high"

    def test_claims_result(self):
        r = ClaimsResult(
            hits=[],
            require_sourcing_topics=["latency"],
            summary="No issues.",
        )
        assert r.require_sourcing_topics == ["latency"]

    def test_guidance_result(self):
        g = GuidanceResult(guidance="prompt", draft="text", source="osp:editing-codes")
        assert g.source == "osp:editing-codes"

    def test_review_brief_serialization(self):
        brief = ReviewBrief(
            audience="dp",
            content_type="blog_post",
            osp_source_sha="abc123",
            execution_plan=["1. glossary", "2. audience"],
            sections=[
                ReviewSection(name="glossary", payload={"hits": []}),
            ],
        )
        d = brief.model_dump()
        assert d["audience"] == "dp"
        assert d["sections"][0]["name"] == "glossary"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the models**

Create `src/cyanview_osp_writer/tools/__init__.py` (empty).

Create `src/cyanview_osp_writer/tools/models.py`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/tools/test_models.py -v`
Expected: PASS, all 6 tests green.

- [ ] **Step 5: Commit**

```bash
git add src/cyanview_osp_writer/tools/ tests/tools/
git commit -m "feat: add shared pydantic output models for tools"
```

---

## Task 11: Logging Setup

**Files:**
- Modify: `src/cyanview_osp_writer/server.py`

Add structured stderr logging via `structlog`. One line per tool call. Never log draft text — log length only.

- [ ] **Step 1: Modify `server.py`**

Replace the top of `src/cyanview_osp_writer/server.py` with:

```python
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
```

- [ ] **Step 2: Verify**

Run:
```bash
uv run python -c "from cyanview_osp_writer.server import build_server; build_server()" 2>&1 | head -3
```
Expected: a JSON log line on stderr with `"event": "resources_loaded"`, glossary_terms count, etc.

- [ ] **Step 3: Commit**

```bash
git add src/cyanview_osp_writer/server.py
git commit -m "feat: configure structlog stderr JSON logging"
```

---

## Task 12: `check_glossary` Tool

**Files:**
- Create: `src/cyanview_osp_writer/tools/check_glossary.py`
- Create: `tests/tools/test_check_glossary.py`
- Modify: `src/cyanview_osp_writer/server.py` (register the tool)

- [ ] **Step 1: Write the failing test**

Create `tests/tools/test_check_glossary.py`:

```python
"""Tests for the check_glossary tool."""

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.check_glossary import check_glossary
from cyanview_osp_writer.tools.models import GlossaryResult


class TestCheckGlossary:
    def test_clean_text_returns_no_hits(self):
        result = check_glossary("The Cyanview RCP is a camera control system.")
        assert isinstance(result, GlossaryResult)
        assert result.hits == []
        assert "no glossary" in result.summary.lower()

    def test_violations_detected(self):
        result = check_glossary("The CyanView remote panel uses RioLive.")
        canonicals = {h.canonical for h in result.hits}
        assert "Cyanview" in canonicals
        assert "RCP" in canonicals
        assert "RIO Live" in canonicals
        assert str(len(result.hits)) in result.summary

    def test_resources_loaded_lazily(self):
        # Just ensure the function works without explicit setup.
        load_resources()
        check_glossary("hello")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_check_glossary.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the tool**

Create `src/cyanview_osp_writer/tools/check_glossary.py`:

```python
"""check_glossary tool — deterministic glossary scan."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.layers.glossary import GlossaryEngine
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GlossaryHitOut, GlossaryResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def check_glossary(text: str) -> GlossaryResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call check_glossary per section."
        )
    resources = load_resources()
    engine = GlossaryEngine(resources.glossary)
    hits = engine.scan(text)
    out = [
        GlossaryHitOut(
            canonical=h.canonical,
            matched_text=h.matched_text,
            start=h.start,
            end=h.end,
            note=h.note,
        )
        for h in hits
    ]
    summary = (
        "No glossary issues found."
        if not out
        else f"Found {len(out)} glossary issue(s) — see hits for details."
    )
    logger.info("tool_call", tool="check_glossary", text_chars=len(text), hits=len(out))
    return GlossaryResult(hits=out, summary=summary)
```

- [ ] **Step 4: Register in `server.py`**

Modify `src/cyanview_osp_writer/server.py`. Add inside `build_server()`, after `server = FastMCP("cyanview-osp-writer")`:

```python
    from cyanview_osp_writer.tools.check_glossary import check_glossary

    @server.tool()
    def check_glossary_tool(text: str) -> dict:
        """Run the Cyanview glossary regex layer over text and return structured hits."""
        return check_glossary(text).model_dump()
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/tools/test_check_glossary.py -v`
Expected: PASS, all 3 tests green.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/tools/check_glossary.py tests/tools/test_check_glossary.py src/cyanview_osp_writer/server.py
git commit -m "feat: add check_glossary tool"
```

---

## Task 13: `check_claims` Tool

**Files:**
- Create: `src/cyanview_osp_writer/tools/check_claims.py`
- Create: `tests/tools/test_check_claims.py`
- Modify: `src/cyanview_osp_writer/server.py`

- [ ] **Step 1: Write the failing test**

Create `tests/tools/test_check_claims.py`:

```python
"""Tests for the check_claims tool."""

import pytest

from cyanview_osp_writer.tools.check_claims import MAX_TEXT_CHARS, check_claims
from cyanview_osp_writer.tools.models import ClaimsResult


class TestCheckClaims:
    def test_clean_text(self):
        r = check_claims("The Cyanview RCP supports SDI workflows.")
        assert isinstance(r, ClaimsResult)
        assert r.hits == []
        assert "latency numbers" in r.require_sourcing_topics

    def test_violations_detected(self):
        r = check_claims(
            "Our revolutionary system delivers zero-latency performance."
        )
        matched = {h.matched_text.lower() for h in r.hits}
        assert "revolutionary" in matched
        assert "zero-latency" in matched

    def test_text_too_long_raises(self):
        with pytest.raises(ValueError, match="text_too_long"):
            check_claims("x" * (MAX_TEXT_CHARS + 1))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_check_claims.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the tool**

Create `src/cyanview_osp_writer/tools/check_claims.py`:

```python
"""check_claims tool — deterministic claims scan."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.layers.claims import ClaimsEngine
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import ClaimsHitOut, ClaimsResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def check_claims(text: str) -> ClaimsResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call check_claims per section."
        )
    resources = load_resources()
    engine = ClaimsEngine(resources.claims)
    hits = engine.scan(text)
    out = [
        ClaimsHitOut(
            matched_text=h.matched_text,
            start=h.start,
            end=h.end,
            category=h.category,
            severity=h.severity,
            reason=h.reason,
        )
        for h in hits
    ]
    summary = (
        "No claims issues found."
        if not out
        else f"Found {len(out)} claim issue(s) — review severity high items first."
    )
    logger.info("tool_call", tool="check_claims", text_chars=len(text), hits=len(out))
    return ClaimsResult(
        hits=out,
        require_sourcing_topics=engine.require_sourcing_topics,
        summary=summary,
    )
```

- [ ] **Step 4: Register in `server.py`**

Add inside `build_server()`:

```python
    from cyanview_osp_writer.tools.check_claims import check_claims

    @server.tool()
    def check_claims_tool(text: str) -> dict:
        """Run the Cyanview claims regex layer over text and return structured hits."""
        return check_claims(text).model_dump()
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/tools/test_check_claims.py -v`
Expected: PASS, all 3 tests green.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/tools/check_claims.py tests/tools/test_check_claims.py src/cyanview_osp_writer/server.py
git commit -m "feat: add check_claims tool"
```

---

## Task 14: `check_audience` Tool

**Files:**
- Create: `src/cyanview_osp_writer/tools/check_audience.py`
- Create: `tests/tools/test_check_audience.py`
- Modify: `src/cyanview_osp_writer/server.py`

- [ ] **Step 1: Write the failing test**

Create `tests/tools/test_check_audience.py`:

```python
"""Tests for the check_audience tool."""

import pytest

from cyanview_osp_writer.tools.check_audience import check_audience
from cyanview_osp_writer.tools.models import GuidanceResult


class TestCheckAudience:
    def test_dp_audience(self):
        r = check_audience("draft text", audience="dp")
        assert isinstance(r, GuidanceResult)
        assert r.draft == "draft text"
        assert "Director of Photography" in r.guidance
        assert r.source == "cyanview:audience:dp"

    def test_mixed_audience(self):
        r = check_audience("draft", audience="mixed")
        assert "Director of Photography" in r.guidance
        assert "Broadcast" in r.guidance
        assert "Rental House" in r.guidance
        assert r.source == "cyanview:audience:mixed"

    def test_invalid_audience(self):
        with pytest.raises(ValueError, match="invalid_audience"):
            check_audience("draft", audience="director")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_check_audience.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the tool**

Create `src/cyanview_osp_writer/tools/check_audience.py`:

```python
"""check_audience tool — assemble audience-aware review prompt."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.layers.audience import AudienceLayer
from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)

VALID_AUDIENCES = {"dp", "broadcast_engineer", "rental_house", "mixed"}
MAX_TEXT_CHARS = 50_000


def check_audience(text: str, audience: str) -> GuidanceResult:
    if audience not in VALID_AUDIENCES:
        raise ValueError(
            f"invalid_audience: {audience!r}; must be one of {sorted(VALID_AUDIENCES)}"
        )
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call check_audience per section."
        )
    resources = load_resources()
    layer = AudienceLayer(resources.audiences)
    review = layer.assemble(text, audience=audience)
    logger.info(
        "tool_call",
        tool="check_audience",
        audience=audience,
        text_chars=len(text),
    )
    return GuidanceResult(
        guidance=review.guidance,
        draft=text,
        source=f"cyanview:audience:{audience}",
    )
```

- [ ] **Step 4: Register in `server.py`**

Add inside `build_server()`:

```python
    from cyanview_osp_writer.tools.check_audience import check_audience

    @server.tool()
    def check_audience_tool(text: str, audience: str) -> dict:
        """Assemble an audience-tone review prompt for the host LLM."""
        return check_audience(text, audience).model_dump()
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/tools/test_check_audience.py -v`
Expected: PASS, all 3 tests green.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/tools/check_audience.py tests/tools/test_check_audience.py src/cyanview_osp_writer/server.py
git commit -m "feat: add check_audience tool"
```

---

## Task 15: `osp_edit` Tool

**Files:**
- Create: `src/cyanview_osp_writer/tools/osp_edit.py`
- Create: `tests/tools/test_osp_edit.py`
- Modify: `src/cyanview_osp_writer/server.py`

- [ ] **Step 1: Write the failing test**

Create `tests/tools/test_osp_edit.py`:

```python
"""Tests for the osp_edit tool."""

import pytest

from cyanview_osp_writer.tools.models import GuidanceResult
from cyanview_osp_writer.tools.osp_edit import MAX_TEXT_CHARS, osp_edit


class TestOspEdit:
    def test_returns_guidance_with_draft(self):
        r = osp_edit("Some draft text.")
        assert isinstance(r, GuidanceResult)
        assert r.draft == "Some draft text."
        assert r.source == "osp:editing-codes"
        assert len(r.guidance) > 0
        assert "placeholder" in r.guidance.lower() or "editing" in r.guidance.lower()

    def test_text_too_long(self):
        with pytest.raises(ValueError, match="text_too_long"):
            osp_edit("x" * (MAX_TEXT_CHARS + 1))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_osp_edit.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the tool**

Create `src/cyanview_osp_writer/tools/osp_edit.py`:

```python
"""osp_edit tool — return OSP Editing Codes guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def osp_edit(text: str) -> GuidanceResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call osp_edit per section."
        )
    resources = load_resources()
    guidance = resources.osp_guides["editing-codes"]
    logger.info("tool_call", tool="osp_edit", text_chars=len(text))
    return GuidanceResult(
        guidance=guidance,
        draft=text,
        source="osp:editing-codes",
    )
```

- [ ] **Step 4: Register in `server.py`**

Add inside `build_server()`:

```python
    from cyanview_osp_writer.tools.osp_edit import osp_edit

    @server.tool()
    def osp_edit_tool(text: str) -> dict:
        """Return OSP Editing Codes guidance plus the draft for a host-LLM editing pass."""
        return osp_edit(text).model_dump()
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/tools/test_osp_edit.py -v`
Expected: PASS, both tests green.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/tools/osp_edit.py tests/tools/test_osp_edit.py src/cyanview_osp_writer/server.py
git commit -m "feat: add osp_edit tool"
```

---

## Task 16: `osp_seo` Tool

**Files:**
- Create: `src/cyanview_osp_writer/tools/osp_seo.py`
- Create: `tests/tools/test_osp_seo.py`
- Modify: `src/cyanview_osp_writer/server.py`

- [ ] **Step 1: Write the failing test**

Create `tests/tools/test_osp_seo.py`:

```python
"""Tests for the osp_seo tool."""

from cyanview_osp_writer.tools.models import GuidanceResult
from cyanview_osp_writer.tools.osp_seo import osp_seo


class TestOspSeo:
    def test_no_keywords(self):
        r = osp_seo("Some draft text.")
        assert isinstance(r, GuidanceResult)
        assert r.source == "osp:seo-guide"
        assert "target keywords" not in r.guidance.lower() or "(none)" in r.guidance.lower()

    def test_with_keywords(self):
        r = osp_seo("Some draft.", target_keywords=["camera control", "broadcast"])
        assert "camera control" in r.guidance
        assert "broadcast" in r.guidance
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_osp_seo.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the tool**

Create `src/cyanview_osp_writer/tools/osp_seo.py`:

```python
"""osp_seo tool — return OSP On-Page SEO guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def osp_seo(text: str, target_keywords: list[str] | None = None) -> GuidanceResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call osp_seo per section."
        )
    resources = load_resources()
    base_guidance = resources.osp_guides["seo-guide"]
    keywords_block = (
        f"\n\nTarget keywords: {', '.join(target_keywords)}\n"
        if target_keywords
        else "\n\nTarget keywords: (none — infer from draft topic)\n"
    )
    guidance = base_guidance + keywords_block
    logger.info(
        "tool_call",
        tool="osp_seo",
        text_chars=len(text),
        keywords=len(target_keywords or []),
    )
    return GuidanceResult(guidance=guidance, draft=text, source="osp:seo-guide")
```

- [ ] **Step 4: Register in `server.py`**

```python
    from cyanview_osp_writer.tools.osp_seo import osp_seo

    @server.tool()
    def osp_seo_tool(text: str, target_keywords: list[str] | None = None) -> dict:
        """Return OSP On-Page SEO guidance plus the draft, optionally with target keywords."""
        return osp_seo(text, target_keywords).model_dump()
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/tools/test_osp_seo.py -v`
Expected: PASS, both tests green.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/tools/osp_seo.py tests/tools/test_osp_seo.py src/cyanview_osp_writer/server.py
git commit -m "feat: add osp_seo tool"
```

---

## Task 17: `osp_meta` Tool

**Files:**
- Create: `src/cyanview_osp_writer/tools/osp_meta.py`
- Create: `tests/tools/test_osp_meta.py`
- Modify: `src/cyanview_osp_writer/server.py`

- [ ] **Step 1: Write the failing test**

Create `tests/tools/test_osp_meta.py`:

```python
"""Tests for the osp_meta tool."""

from cyanview_osp_writer.tools.models import GuidanceResult
from cyanview_osp_writer.tools.osp_meta import osp_meta


class TestOspMeta:
    def test_returns_guidance_and_draft(self):
        r = osp_meta("Draft body.")
        assert isinstance(r, GuidanceResult)
        assert r.source == "osp:meta-guide"
        assert r.draft == "Draft body."
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_osp_meta.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Implement the tool**

Create `src/cyanview_osp_writer/tools/osp_meta.py`:

```python
"""osp_meta tool — return OSP Meta-information guidance + draft."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.models import GuidanceResult

logger = structlog.get_logger(__name__)

MAX_TEXT_CHARS = 50_000


def osp_meta(text: str) -> GuidanceResult:
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call osp_meta per section."
        )
    resources = load_resources()
    guidance = resources.osp_guides["meta-guide"]
    logger.info("tool_call", tool="osp_meta", text_chars=len(text))
    return GuidanceResult(guidance=guidance, draft=text, source="osp:meta-guide")
```

- [ ] **Step 4: Register in `server.py`**

```python
    from cyanview_osp_writer.tools.osp_meta import osp_meta

    @server.tool()
    def osp_meta_tool(text: str) -> dict:
        """Return OSP Meta-information guidance plus the draft."""
        return osp_meta(text).model_dump()
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/tools/test_osp_meta.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/cyanview_osp_writer/tools/osp_meta.py tests/tools/test_osp_meta.py src/cyanview_osp_writer/server.py
git commit -m "feat: add osp_meta tool"
```

---

## Task 18: `review_draft` Orchestrator

**Files:**
- Create: `src/cyanview_osp_writer/tools/review_draft.py`
- Create: `tests/tools/test_review_draft.py`
- Create: `tests/fixtures/drafts/mixed_violations.md`
- Modify: `src/cyanview_osp_writer/server.py`

The orchestrator runs all six layers in order and returns one structured `ReviewBrief`. Sub-tools remain available for re-runs.

- [ ] **Step 1: Create mixed-violations fixture**

`tests/fixtures/drafts/mixed_violations.md`:

```markdown
# Why CyanView is industry-leading

The CyanView remote panel is a revolutionary camera remote that delivers zero-latency performance. It's seamless and works with every camera ever made.
```

- [ ] **Step 2: Write the failing test**

Create `tests/tools/test_review_draft.py`:

```python
"""Tests for the review_draft orchestrator."""

from pathlib import Path

import pytest

from cyanview_osp_writer.tools.models import ReviewBrief
from cyanview_osp_writer.tools.review_draft import (
    VALID_AUDIENCES,
    VALID_CONTENT_TYPES,
    review_draft,
)


class TestReviewDraft:
    def test_returns_review_brief(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="broadcast_engineer", content_type="blog_post"
        )
        assert isinstance(brief, ReviewBrief)
        assert brief.audience == "broadcast_engineer"
        assert brief.content_type == "blog_post"
        assert len(brief.sections) > 0

    def test_sections_in_expected_order(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        names = [s.name for s in brief.sections]
        assert names == [
            "glossary",
            "claims",
            "audience",
            "osp_edit",
            "osp_seo",
            "osp_meta",
        ]

    def test_glossary_section_contains_hits(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        glossary = next(s for s in brief.sections if s.name == "glossary")
        assert glossary.payload["hits"]
        canonicals = {h["canonical"] for h in glossary.payload["hits"]}
        assert "Cyanview" in canonicals

    def test_claims_section_contains_hits(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        claims = next(s for s in brief.sections if s.name == "claims")
        matched = {h["matched_text"].lower() for h in claims.payload["hits"]}
        assert "industry-leading" in matched or "revolutionary" in matched

    def test_audience_section_contains_guidance(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="broadcast_engineer", content_type="blog_post"
        )
        audience = next(s for s in brief.sections if s.name == "audience")
        assert "Broadcast" in audience.payload["guidance"]

    def test_focus_filters_sections(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text,
            audience="dp",
            content_type="blog_post",
            focus=["glossary", "claims"],
        )
        names = {s.name for s in brief.sections}
        assert names == {"glossary", "claims"}

    def test_invalid_audience_rejected(self):
        with pytest.raises(ValueError, match="invalid_audience"):
            review_draft(text="x", audience="director", content_type="blog_post")

    def test_invalid_content_type_rejected(self):
        with pytest.raises(ValueError, match="invalid_content_type"):
            review_draft(text="x", audience="dp", content_type="tweet")

    def test_invalid_focus_rejected(self):
        with pytest.raises(ValueError, match="invalid_focus"):
            review_draft(
                text="x", audience="dp", content_type="blog_post", focus=["typos"]
            )

    def test_text_too_long(self):
        with pytest.raises(ValueError, match="text_too_long"):
            review_draft(
                text="x" * 60_000, audience="dp", content_type="blog_post"
            )

    def test_execution_plan_present(self, fixtures_dir: Path):
        text = (fixtures_dir / "drafts" / "mixed_violations.md").read_text()
        brief = review_draft(
            text=text, audience="dp", content_type="blog_post"
        )
        assert len(brief.execution_plan) >= 1
        assert all(isinstance(s, str) for s in brief.execution_plan)

    def test_constants_exposed(self):
        assert "dp" in VALID_AUDIENCES
        assert "blog_post" in VALID_CONTENT_TYPES
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest tests/tools/test_review_draft.py -v`
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: Implement the orchestrator**

Create `src/cyanview_osp_writer/tools/review_draft.py`:

```python
"""review_draft orchestrator — runs all six layers and returns a ReviewBrief."""

from __future__ import annotations

import structlog

from cyanview_osp_writer.resources import load_resources
from cyanview_osp_writer.tools.check_audience import check_audience
from cyanview_osp_writer.tools.check_claims import check_claims
from cyanview_osp_writer.tools.check_glossary import check_glossary
from cyanview_osp_writer.tools.models import ReviewBrief, ReviewSection
from cyanview_osp_writer.tools.osp_edit import osp_edit
from cyanview_osp_writer.tools.osp_meta import osp_meta
from cyanview_osp_writer.tools.osp_seo import osp_seo

logger = structlog.get_logger(__name__)

VALID_AUDIENCES = {"dp", "broadcast_engineer", "rental_house", "mixed"}
VALID_CONTENT_TYPES = {
    "landing_page",
    "blog_post",
    "product_brief",
    "release_note",
    "other",
}
VALID_FOCUS = ("glossary", "claims", "audience", "osp_edit", "osp_seo", "osp_meta")
MAX_TEXT_CHARS = 50_000


def _build_execution_plan(active: list[str], audience: str) -> list[str]:
    plan: list[str] = [
        "1. Read the structured sections below as your marching orders.",
        f"2. Render the review for audience={audience}.",
    ]
    step = 3
    if "glossary" in active:
        plan.append(
            f"{step}. Apply glossary hits inline: show each rejected term with its canonical replacement."
        )
        step += 1
    if "claims" in active:
        plan.append(
            f"{step}. Apply claims hits: rewrite each high-severity superlative or unsourced technical claim."
        )
        step += 1
    if "audience" in active:
        plan.append(
            f"{step}. Apply audience guidance: flag tone mismatches and assumed-knowledge gaps for the named audience."
        )
        step += 1
    if "osp_edit" in active:
        plan.append(
            f"{step}. Apply OSP Editing Codes: produce a code-tagged review with before/after suggestions."
        )
        step += 1
    if "osp_seo" in active:
        plan.append(
            f"{step}. Apply OSP On-Page SEO: suggest keyword integration and structure improvements."
        )
        step += 1
    if "osp_meta" in active:
        plan.append(
            f"{step}. Apply OSP Meta guide: produce H1, meta title (50-60), meta description (155-160), slug."
        )
        step += 1
    plan.append(f"{step}. Summarise the top 3 most-impactful changes at the end.")
    return plan


def review_draft(
    text: str,
    audience: str,
    content_type: str,
    focus: list[str] | None = None,
) -> ReviewBrief:
    if audience not in VALID_AUDIENCES:
        raise ValueError(
            f"invalid_audience: {audience!r}; must be one of {sorted(VALID_AUDIENCES)}"
        )
    if content_type not in VALID_CONTENT_TYPES:
        raise ValueError(
            f"invalid_content_type: {content_type!r}; must be one of {sorted(VALID_CONTENT_TYPES)}"
        )
    if len(text) > MAX_TEXT_CHARS:
        raise ValueError(
            f"text_too_long: {len(text)} > {MAX_TEXT_CHARS}; "
            "split into sections and call review_draft per section."
        )
    if focus is not None:
        invalid = [f for f in focus if f not in VALID_FOCUS]
        if invalid:
            raise ValueError(
                f"invalid_focus: {invalid!r}; must be subset of {list(VALID_FOCUS)}"
            )
        active = [f for f in VALID_FOCUS if f in focus]
    else:
        active = list(VALID_FOCUS)

    resources = load_resources()
    sections: list[ReviewSection] = []

    if "glossary" in active:
        sections.append(
            ReviewSection(
                name="glossary", payload=check_glossary(text).model_dump()
            )
        )
    if "claims" in active:
        sections.append(
            ReviewSection(name="claims", payload=check_claims(text).model_dump())
        )
    if "audience" in active:
        sections.append(
            ReviewSection(
                name="audience",
                payload=check_audience(text, audience=audience).model_dump(),
            )
        )
    if "osp_edit" in active:
        sections.append(
            ReviewSection(name="osp_edit", payload=osp_edit(text).model_dump())
        )
    if "osp_seo" in active:
        sections.append(
            ReviewSection(name="osp_seo", payload=osp_seo(text).model_dump())
        )
    if "osp_meta" in active:
        sections.append(
            ReviewSection(name="osp_meta", payload=osp_meta(text).model_dump())
        )

    brief = ReviewBrief(
        audience=audience,
        content_type=content_type,
        osp_source_sha=resources.osp_source_sha,
        execution_plan=_build_execution_plan(active, audience),
        sections=sections,
    )
    logger.info(
        "tool_call",
        tool="review_draft",
        audience=audience,
        content_type=content_type,
        text_chars=len(text),
        sections=[s.name for s in sections],
    )
    return brief
```

- [ ] **Step 5: Register in `server.py`**

Add inside `build_server()`:

```python
    from cyanview_osp_writer.tools.review_draft import review_draft

    @server.tool()
    def review_draft_tool(
        text: str,
        audience: str,
        content_type: str,
        focus: list[str] | None = None,
    ) -> dict:
        """Run the full Cyanview + OSP review pipeline and return a structured ReviewBrief.

        audience: one of "dp", "broadcast_engineer", "rental_house", "mixed"
        content_type: one of "landing_page", "blog_post", "product_brief", "release_note", "other"
        focus: optional subset of ["glossary","claims","audience","osp_edit","osp_seo","osp_meta"]
        """
        return review_draft(text, audience, content_type, focus).model_dump()
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/tools/test_review_draft.py -v`
Expected: PASS, all 12 tests green.

- [ ] **Step 7: Run the full test suite**

Run: `uv run pytest -q`
Expected: all tests green.

- [ ] **Step 8: Commit**

```bash
git add src/cyanview_osp_writer/tools/review_draft.py tests/tools/test_review_draft.py tests/fixtures/drafts/mixed_violations.md src/cyanview_osp_writer/server.py
git commit -m "feat: add review_draft orchestrator running all six layers"
```

---

## Task 19: MCP Resources (read-only)

**Files:**
- Modify: `src/cyanview_osp_writer/server.py`

Expose the bundled YAML and OSP markdown files as MCP resources so a host can list and read them.

- [ ] **Step 1: Modify `server.py` — register resources**

Inside `build_server()`, after the tool registrations, add:

```python
    @server.resource("cyanview://glossary.yaml")
    def _glossary_resource() -> str:
        from importlib import resources as ir

        return (
            ir.files("cyanview_osp_writer.resources")
            .joinpath("cyanview")
            .joinpath("glossary.yaml")
            .read_text(encoding="utf-8")
        )

    @server.resource("cyanview://audiences.yaml")
    def _audiences_resource() -> str:
        from importlib import resources as ir

        return (
            ir.files("cyanview_osp_writer.resources")
            .joinpath("cyanview")
            .joinpath("audiences.yaml")
            .read_text(encoding="utf-8")
        )

    @server.resource("cyanview://claims-patterns.yaml")
    def _claims_resource() -> str:
        from importlib import resources as ir

        return (
            ir.files("cyanview_osp_writer.resources")
            .joinpath("cyanview")
            .joinpath("claims-patterns.yaml")
            .read_text(encoding="utf-8")
        )

    for _name in ("writing-guide", "editing-codes", "seo-guide", "meta-guide", "value-map"):
        def _make(name: str):
            @server.resource(f"osp://{name}.md")
            def _osp_resource() -> str:
                return resources.osp_guides[name]

            return _osp_resource

        _make(_name)
```

- [ ] **Step 2: Smoke test**

Run:
```bash
uv run python -c "
from cyanview_osp_writer.server import build_server
s = build_server()
print('built ok:', s.name)
"
```
Expected: prints `built ok: cyanview-osp-writer`.

- [ ] **Step 3: Commit**

```bash
git add src/cyanview_osp_writer/server.py
git commit -m "feat: expose cyanview and OSP resources via MCP"
```

---

## Task 20: Server-Startup Integration Test

**Files:**
- Create: `tests/integration/__init__.py`
- Create: `tests/integration/test_server_startup.py`

- [ ] **Step 1: Write the test**

Create `tests/integration/__init__.py` (empty).

Create `tests/integration/test_server_startup.py`:

```python
"""Integration: server startup, tool registry, resource registry."""

import pytest

from cyanview_osp_writer.server import build_server


@pytest.fixture
def server():
    return build_server()


class TestServerStartup:
    def test_server_built(self, server):
        assert server.name == "cyanview-osp-writer"

    @pytest.mark.asyncio
    async def test_tools_registered(self, server):
        tools = await server.list_tools()
        names = {t.name for t in tools}
        expected = {
            "check_glossary_tool",
            "check_claims_tool",
            "check_audience_tool",
            "osp_edit_tool",
            "osp_seo_tool",
            "osp_meta_tool",
            "review_draft_tool",
        }
        assert expected.issubset(names)

    @pytest.mark.asyncio
    async def test_resources_registered(self, server):
        resources = await server.list_resources()
        uris = {str(r.uri) for r in resources}
        assert "cyanview://glossary.yaml" in uris
        assert "cyanview://audiences.yaml" in uris
        assert "cyanview://claims-patterns.yaml" in uris
        assert "osp://writing-guide.md" in uris
        assert "osp://editing-codes.md" in uris
        assert "osp://seo-guide.md" in uris
        assert "osp://meta-guide.md" in uris
        assert "osp://value-map.md" in uris
```

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/integration/test_server_startup.py -v`
Expected: PASS, all 3 tests green.

If `list_tools` / `list_resources` are not directly available on `FastMCP`, replace with the equivalent introspection (`server._tool_manager._tools.keys()` etc.) — verify the API at run time and adjust the test.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/__init__.py tests/integration/test_server_startup.py
git commit -m "test: integration test for server startup, tools, resources"
```

---

## Task 21: Resource-Validation Integration Test

**Files:**
- Create: `tests/integration/test_resource_validation.py`

This test catches drift in the bundled YAML / OSP markdown files. It runs on every CI build.

- [ ] **Step 1: Write the test**

Create `tests/integration/test_resource_validation.py`:

```python
"""Integration: bundled resource files are well-formed."""

import yaml

from cyanview_osp_writer.resources import OSP_GUIDE_NAMES, load_resources
from cyanview_osp_writer.schemas import (
    AudiencesFile,
    ClaimsFile,
    GlossaryFile,
)


class TestResourceValidation:
    def test_glossary_yaml_parses(self):
        r = load_resources()
        assert isinstance(r.glossary, GlossaryFile)
        assert len(r.glossary.terms) >= 5

    def test_audiences_yaml_parses(self):
        r = load_resources()
        assert isinstance(r.audiences, AudiencesFile)

    def test_claims_yaml_parses(self):
        r = load_resources()
        assert isinstance(r.claims, ClaimsFile)
        assert len(r.claims.banned_superlatives) >= 1

    def test_osp_guides_present_and_nonempty(self):
        r = load_resources()
        for name in OSP_GUIDE_NAMES:
            assert name in r.osp_guides, f"missing OSP guide: {name}"
            content = r.osp_guides[name]
            assert len(content.strip()) > 0, f"empty OSP guide: {name}"
            assert content.startswith("#"), f"OSP guide missing markdown header: {name}"

    def test_osp_source_sha_present(self):
        r = load_resources()
        assert r.osp_source_sha
        # Either "placeholder" (pre-sync) or a 40-char SHA — both acceptable.
        assert r.osp_source_sha == "placeholder" or len(r.osp_source_sha) == 40
```

- [ ] **Step 2: Run the test**

Run: `uv run pytest tests/integration/test_resource_validation.py -v`
Expected: PASS, all 5 tests green.

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_resource_validation.py
git commit -m "test: integration test for bundled resource validation"
```

---

## Task 22: GitHub Actions — Test Workflow

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Create the workflow**

```yaml
name: test

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Run ruff
        run: uv run ruff check src tests

      - name: Run pytest with coverage
        run: uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add test workflow with coverage gate"
```

---

## Task 23: Sync Script + CI

**Files:**
- Create: `scripts/sync_osp.py`
- Create: `.github/workflows/sync-osp.yml`
- Create: `tests/fixtures/osp_snapshot/README.md`
- Create: `tests/integration/test_sync_script.py`

The sync script clones the upstream OSP repo, extracts guidance text from upstream Python modules, and writes the markdown files. Tested against a frozen fixture so we don't hit the network in CI.

- [ ] **Step 1: Create the snapshot README placeholder**

`tests/fixtures/osp_snapshot/README.md`:

```markdown
# OSP Upstream Snapshot Fixture

This directory holds a frozen copy of the OSP upstream Python module(s)
used by `tests/integration/test_sync_script.py`. To refresh:

```bash
git clone --depth 1 https://github.com/open-strategy-partners/osp_marketing_tools /tmp/osp-upstream
cp /tmp/osp-upstream/src/osp_marketing_tools/server.py tests/fixtures/osp_snapshot/server.py
```

(Adjust the source path if upstream restructures.)
```

- [ ] **Step 2: Create `scripts/sync_osp.py`**

```python
"""Sync OSP upstream guidance into bundled markdown resources.

Strategy:
1. Clone upstream into a temp dir (or use a local snapshot path).
2. Import upstream Python modules and extract module-level constants
   that hold guidance text.
3. Write each guide to src/cyanview_osp_writer/resources/osp/<name>.md.
4. Record the upstream commit SHA in .source-sha.
5. Update ATTRIBUTION.md with the sync date and SHA.

Mapping from upstream constant names to our guide files is defined in
GUIDE_MAP. If upstream renames a constant, update this map.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_URL = "https://github.com/open-strategy-partners/osp_marketing_tools"
DEFAULT_CLONE_DIR = Path("/tmp/osp-upstream")

# Upstream module path (relative to clone root) → constant name → our guide name.
# If upstream restructures, edit this map.
GUIDE_MAP: dict[tuple[str, str], str] = {
    ("src/osp_marketing_tools/server.py", "WRITING_GUIDE"): "writing-guide",
    ("src/osp_marketing_tools/server.py", "EDITING_CODES"): "editing-codes",
    ("src/osp_marketing_tools/server.py", "SEO_GUIDE"): "seo-guide",
    ("src/osp_marketing_tools/server.py", "META_GUIDE"): "meta-guide",
    ("src/osp_marketing_tools/server.py", "VALUE_MAP_GUIDE"): "value-map",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCES_OSP = PROJECT_ROOT / "src" / "cyanview_osp_writer" / "resources" / "osp"


def _git_clone(target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    subprocess.run(
        ["git", "clone", "--depth", "1", REPO_URL, str(target)],
        check=True,
    )


def _git_sha(repo: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return out.stdout.strip()


def _import_upstream(module_path: Path):
    spec = importlib.util.spec_from_file_location("_osp_upstream", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module spec for {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extract(clone_root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for (rel_path, const_name), guide_name in GUIDE_MAP.items():
        module_path = clone_root / rel_path
        if not module_path.exists():
            raise RuntimeError(
                f"Expected upstream module not found: {module_path}. "
                f"Update GUIDE_MAP in scripts/sync_osp.py."
            )
        module = _import_upstream(module_path)
        if not hasattr(module, const_name):
            raise RuntimeError(
                f"Upstream module {rel_path} does not define {const_name}. "
                f"Update GUIDE_MAP in scripts/sync_osp.py."
            )
        text = getattr(module, const_name)
        if not isinstance(text, str):
            raise RuntimeError(
                f"Upstream constant {const_name} is not a string."
            )
        out[guide_name] = text
    return out


def _write_guides(guides: dict[str, str]) -> None:
    RESOURCES_OSP.mkdir(parents=True, exist_ok=True)
    for name, text in guides.items():
        path = RESOURCES_OSP / f"{name}.md"
        if not text.startswith("#"):
            text = f"# OSP {name}\n\n" + text
        path.write_text(text, encoding="utf-8")


def _write_source_sha(sha: str) -> None:
    (RESOURCES_OSP / ".source-sha").write_text(sha + "\n", encoding="utf-8")


def _write_attribution(sha: str) -> None:
    today = datetime.now(timezone.utc).date().isoformat()
    content = f"""# OSP Source Attribution

Files in this directory (other than this one and `.source-sha`) are derived from:

  https://github.com/open-strategy-partners/osp_marketing_tools
  Commit: {sha}
  Synced: {today}

Licensed under Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
https://creativecommons.org/licenses/by-sa/4.0/
"""
    (RESOURCES_OSP / "ATTRIBUTION.md").write_text(content, encoding="utf-8")


def sync(clone_dir: Path) -> str:
    """Run a full sync. Returns the upstream SHA. Used by both CLI and tests."""
    guides = _extract(clone_dir)
    sha = _git_sha(clone_dir)
    _write_guides(guides)
    _write_source_sha(sha)
    _write_attribution(sha)
    return sha


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from",
        dest="source",
        type=Path,
        default=None,
        help="Path to an existing local clone (skip git clone). For tests.",
    )
    args = parser.parse_args()

    if args.source is not None:
        clone_dir = args.source
    else:
        clone_dir = DEFAULT_CLONE_DIR
        _git_clone(clone_dir)

    sha = sync(clone_dir)
    print(f"Synced OSP guidance from commit {sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: Write the integration test**

Create `tests/integration/test_sync_script.py`:

```python
"""Integration: sync_osp script runs against a frozen snapshot fixture."""

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = PROJECT_ROOT / "tests" / "fixtures" / "osp_snapshot"


@pytest.mark.skipif(
    not (SNAPSHOT_DIR / "src" / "osp_marketing_tools" / "server.py").exists(),
    reason="OSP snapshot fixture not yet captured (see tests/fixtures/osp_snapshot/README.md)",
)
def test_sync_script_against_snapshot(tmp_path: Path):
    """Run sync_osp.py against the frozen snapshot, verify guides written."""
    work = tmp_path / "snapshot"
    shutil.copytree(SNAPSHOT_DIR, work)
    # Initialise as a git repo so `git rev-parse HEAD` succeeds.
    subprocess.run(["git", "-C", str(work), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(work), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(work), "-c", "user.email=t@t", "-c", "user.name=t",
         "commit", "-q", "-m", "snapshot"],
        check=True,
    )
    result = subprocess.run(
        ["uv", "run", "python", "scripts/sync_osp.py", "--from", str(work)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    osp_dir = PROJECT_ROOT / "src" / "cyanview_osp_writer" / "resources" / "osp"
    for name in ("writing-guide", "editing-codes", "seo-guide", "meta-guide", "value-map"):
        f = osp_dir / f"{name}.md"
        assert f.exists()
        assert f.read_text().strip()
    sha = (osp_dir / ".source-sha").read_text().strip()
    assert len(sha) == 40
```

- [ ] **Step 4: Create the sync workflow**

`.github/workflows/sync-osp.yml`:

```yaml
name: sync-osp

on:
  schedule:
    - cron: "0 6 * * 1"   # Mondays 06:00 UTC
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Run sync
        run: uv run python scripts/sync_osp.py

      - name: Run tests against synced files
        run: uv run pytest -q

      - name: Open PR if changed
        uses: peter-evans/create-pull-request@v6
        with:
          commit-message: "chore: sync OSP guidance"
          title: "chore: sync OSP guidance"
          body: |
            Automated weekly sync from
            https://github.com/open-strategy-partners/osp_marketing_tools
          branch: chore/sync-osp
          delete-branch: true
```

- [ ] **Step 5: Run the (likely-skipped) test**

Run: `uv run pytest tests/integration/test_sync_script.py -v`
Expected: SKIPPED (snapshot not yet captured).

When the user is ready to capture the snapshot, follow the README instructions in `tests/fixtures/osp_snapshot/README.md`. Once captured, the test runs and locks in sync behavior.

- [ ] **Step 6: Commit**

```bash
git add scripts/sync_osp.py .github/workflows/sync-osp.yml tests/fixtures/osp_snapshot/README.md tests/integration/test_sync_script.py
git commit -m "feat: add OSP sync script with weekly CI workflow"
```

---

## Task 24: README and Final Verification

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create the README**

````markdown
# cyanview-osp-writer

A local stdio MCP server that reviews Cyanview marketing and documentation drafts using the [Open Strategy Partners (OSP)](https://github.com/open-strategy-partners/osp_marketing_tools) writing methodology, layered with Cyanview-specific brand checks.

## What it does

Paste a draft into Claude Code, ask for a review, and the tool returns a structured review brief covering:

- **Glossary** — Cyanview terminology check (deterministic regex)
- **Claims** — banned superlatives + unverifiable technical claims (deterministic regex)
- **Audience** — tone fit for one of three Cyanview audiences (DP, broadcast engineer, rental house)
- **OSP Editing Codes** — semantic editing-code review
- **OSP On-Page SEO** — keyword integration and structure
- **OSP Meta** — H1, meta title, description, slug

## Install

In your Claude Code MCP settings:

```json
"cyanview_osp_writer": {
  "command": "uvx",
  "args": [
    "--from",
    "git+https://github.com/alanogic/cyanview-osp-writer@main",
    "cyanview-osp-writer"
  ]
}
```

No credentials. No environment variables. Pin to a tag once releases are cut.

## Usage

In Claude Code:

> Review this draft for a broadcast engineer audience.
>
> [paste draft]

Claude calls `review_draft_tool(text=..., audience="broadcast_engineer", content_type="blog_post")` and renders the structured review inline. Re-run individual layers (`check_claims_tool`, `osp_seo_tool`, etc.) on revisions.

## Development

```bash
uv sync
uv run pytest
uv run python scripts/sync_osp.py   # refresh OSP guidance from upstream
```

## License

CC BY-SA 4.0. See [LICENSE](LICENSE) and [ATTRIBUTION.md](ATTRIBUTION.md).
````

- [ ] **Step 2: Run the full suite**

Run: `uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=80 -q`
Expected: all tests pass, coverage ≥80%.

- [ ] **Step 3: Lint**

Run: `uv run ruff check src tests`
Expected: clean. If lint errors appear, fix them and re-run.

- [ ] **Step 4: Smoke-test the server end-to-end**

Run:
```bash
uv run python -m cyanview_osp_writer &
SERVER_PID=$!
sleep 1
kill $SERVER_PID
```
Expected: the server starts (you see the `resources_loaded` JSON log line on stderr) and exits cleanly when killed.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add README with install and usage"
```

- [ ] **Step 6: Tag the MVP release**

```bash
git tag -a v0.1.0 -m "MVP: paste-in draft review with OSP + Cyanview layers"
```

(Do **not** push the tag yet — that's a user decision once the repo lives at `alanogic/cyanview-osp-writer`.)

---

## Self-Review Notes

**Spec coverage:**
- §3.1 tool surface — Tasks 12–18 (one tool each, plus orchestrator) ✓
- §3.2 MCP resources — Task 19 ✓
- §3.3 execution model (tools return prompts, host LLM does the work) — encoded in every tool returning `GuidanceResult` or structured hits, never rendered review text ✓
- §4 Cyanview layer data shapes — Tasks 2 (schemas), 3 (seed YAML), 4–6 (engines) ✓
- §5 OSP bundling & sync — Tasks 8 (placeholders), 23 (sync script + CI) ✓
- §6 error handling — Pydantic input validation in every tool, regex timeout in §4–5, eager startup load in Task 7+9, structlog stderr in Task 11, draft text never logged (only `text_chars`) ✓
- §7 testing — unit (Tasks 4–6), tool (Tasks 12–18), integration (Tasks 20, 21, 23), CI (Task 22) ✓
- §8 project layout — matches Tasks 1–24 file paths ✓
- §9 packaging — Task 1 (`pyproject.toml`) ✓
- §10 day-to-day usage — README in Task 24 ✓
- §11 Phase 2 hooks — architecture preserved (each tool is one file; adding `draft_new`, `review_odoo_article`, `review_file` is one new file in `tools/` plus a registry entry) ✓
- §12 open items — `regex>=2024.0` (uses `timeout=`), `mixed` audience kept in MVP ✓

**Placeholder scan:** No "TBD/TODO/fill in" markers in any task. Every code step contains complete code. Every command step contains the exact command and expected output.

**Type consistency:**
- `GlossaryHit` (layer) → `GlossaryHitOut` (tool model) — Task 4 + Task 10 + Task 12 ✓
- `ClaimsHit` → `ClaimsHitOut` — Task 5 + Task 10 + Task 13 ✓
- `AudienceReview.guidance` → `GuidanceResult.guidance` — Task 6 + Task 14 ✓
- `ReviewSection.payload` is `dict[str, Any]` and Task 18's tests inspect via dict access — consistent ✓
- `VALID_AUDIENCES` defined in `review_draft.py` (Task 18) and `check_audience.py` (Task 14) — both contain `mixed` plus the three named audiences. The two definitions are intentional (each tool standalone-validatable); they must stay in sync, which is enforced by the matching tests.
