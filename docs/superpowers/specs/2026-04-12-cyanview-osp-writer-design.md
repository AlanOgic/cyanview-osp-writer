# cyanview-osp-writer — Design Spec

**Date:** 2026-04-12
**Status:** Approved (brainstorming phase complete)
**Repo (planned):** `alanogic/cyanview-osp-writer`
**License:** CC BY-SA 4.0 (matches OSP upstream)

---

## 1. Purpose

A local stdio MCP server, `cyanview-osp-writer`, that reviews Cyanview marketing and documentation drafts using the **Open Strategy Partners (OSP) marketing methodology** layered with **Cyanview-specific brand checks**.

The server wraps OSP's writing/editing/SEO/meta/value-map guidance (bundled, not chained at runtime) and adds three Cyanview-native review layers: terminology glossary, audience tone profile, and unverifiable-claims detection.

Day-to-day workflow: paste a draft into Claude Code → call `review_draft` → get a structured review brief that the host LLM executes against the draft and renders inline.

## 2. Scope

### MVP (Phase 1) — IN
- Paste-in draft review only (no file I/O, no Odoo).
- Single orchestrator tool `review_draft` plus six sub-tools for re-running individual layers.
- OSP guidance bundled as MCP resources (synced from upstream weekly via CI).
- Three Cyanview layers: glossary (deterministic), audience (guidance), claims (deterministic + guidance).
- Claude Code CLI as the MCP host.
- Python 3.11+, packaged for `uvx --from git+...` install.

### Phase 2 — OUT of MVP, architecture supports
- Drafting mode (`draft_new`): pick content type, answer Cyanview-specific questions, walk through OSP Value Map → draft → review pipeline.
- Odoo integration (`review_odoo_article`, write-back via existing Cyanview Odoo MCP).
- Local file I/O (`review_file(path)`).
- Claude Desktop MCP App with rich UI (currently terminal-only).

### Explicitly NOT planned
- Autonomous drafting without human review.
- Multi-language support beyond English (FR/cinematography terms can extend glossary later).
- Scoring/grading engine (OSP methodology is qualitative).
- Visual diff rendering (host LLM markdown output is sufficient for MVP).

## 3. Architecture

### 3.1 Tool surface

**Orchestrator (primary entry point):**

```
review_draft(
  text: str,                              # max ~50k chars / ~12k tokens
  audience: "dp" | "broadcast_engineer" | "rental_house" | "mixed",
  content_type: "landing_page" | "blog_post" | "product_brief" | "release_note" | "other",
  focus: list[str] | None = None          # optional: skip layers, e.g. ["seo", "claims"]
) -> ReviewBrief
```

Returns a structured `ReviewBrief` containing:
- An ordered execution plan for the host LLM.
- One section per active layer: glossary hits, OSP editing-codes guidance + draft, OSP SEO guidance, OSP meta guidance, audience profile + draft, claims hits + guidance.
- A summary header with audience, content_type, and the OSP source SHA.

**Sub-tools (re-run individual layers):**

| Tool | Purpose |
|---|---|
| `osp_edit(text)` | Returns OSP Editing Codes guidance + draft for a host-LLM editing pass. |
| `osp_seo(text, target_keywords?)` | Returns OSP On-Page SEO guidance + draft. |
| `osp_meta(text)` | Returns OSP Meta-information guide + draft for H1/title/description/slug generation. |
| `check_glossary(text)` | Deterministic regex pass over Cyanview glossary; returns structured hits with offsets and canonical suggestions. |
| `check_audience(text, audience)` | Returns audience profile + draft for a host-LLM tone/assumed-knowledge review. |
| `check_claims(text)` | Deterministic regex pass for banned superlatives + technical claims; returns structured hits with severity and reason. |

### 3.2 MCP resources (read-only, bundled)

| URI | Source |
|---|---|
| `cyanview://glossary.yaml` | `resources/cyanview/glossary.yaml` |
| `cyanview://audiences.yaml` | `resources/cyanview/audiences.yaml` |
| `cyanview://claims-patterns.yaml` | `resources/cyanview/claims-patterns.yaml` |
| `osp://writing-guide.md` | `resources/osp/writing-guide.md` (synced) |
| `osp://editing-codes.md` | `resources/osp/editing-codes.md` (synced) |
| `osp://seo-guide.md` | `resources/osp/seo-guide.md` (synced) |
| `osp://meta-guide.md` | `resources/osp/meta-guide.md` (synced) |
| `osp://value-map.md` | `resources/osp/value-map.md` (synced) |

### 3.3 Execution model

Tools return **prompts and structured data, not rendered reviews**. The host LLM (Claude Code) does the actual review work using the tool output as marching orders. This matches OSP's own server pattern and keeps composition with other MCP servers natural.

## 4. Cyanview Layer Data Shapes

All three layers are YAML, bundled as MCP resources, editable without code changes. Each file has a `version: 1` field for future migrations.

### 4.1 `cyanview/glossary.yaml`

```yaml
version: 1
terms:
  - canonical: "RCP"
    full_name: "Remote Control Panel"
    accept: ["RCP", "Remote Control Panel"]
    reject: ["remote panel", "control pad"]
    note: "Always spell out on first use in external content."
  - canonical: "RIO Live"
    accept: ["RIO Live", "RIO-Live"]
    reject: ["RioLive", "Rio"]
    deprecated_aliases: []
  - canonical: "camera control"
    reject: ["camera remote", "camera controller software"]
    note: "Cyanview sells *camera control systems*, not 'remotes'."
```

`check_glossary` runs deterministic regex for `reject` and `deprecated_aliases`, returning hits with line/offset and the canonical form. Fuzzy/contextual cases are passed to the host LLM via a guidance block in the same response.

Seed: ~20 terms for MVP. Source list captured during implementation (from Cyanview website + recent docs).

### 4.2 `cyanview/audiences.yaml`

```yaml
version: 1
audiences:
  dp:
    label: "Director of Photography / Cinematographer"
    assumes: ["cinematic language", "lens/shutter/ISO fluency"]
    avoid: ["deep protocol jargon", "rack-unit talk", "latency numbers without context"]
    tone: "creative, outcome-focused, visual"
  broadcast_engineer:
    label: "Broadcast / Live Engineer"
    assumes: ["SDI/IP workflows", "CCU concepts", "latency budgets"]
    avoid: ["marketing fluff", "vague 'seamless' claims"]
    tone: "precise, spec-driven, skeptical of hype"
  rental_house:
    label: "Rental House / AC"
    assumes: ["gear logistics", "compatibility matrices"]
    avoid: ["abstract workflow talk"]
    tone: "practical, checklist-friendly, compatibility-first"
```

`check_audience` returns the relevant profile plus the draft, instructing the host LLM to flag tone mismatches and assumed-knowledge gaps. The `mixed` audience returns all three profiles with a "note conflicts where they arise" instruction.

### 4.3 `cyanview/claims-patterns.yaml`

```yaml
version: 1
banned_superlatives:
  - pattern: "\\b(industry[- ]leading|first[- ]ever|world['’]?s (best|first)|revolutionary|game[- ]changer)\\b"
    severity: high
    reason: "Unverifiable marketing superlative — rewrite with concrete evidence."
technical_claims_needing_source:
  - pattern: "\\b(sub[- ]?\\d+\\s?ms|zero[- ]latency|unlimited|100%\\s+(compatible|reliable))\\b"
    severity: medium
    reason: "Technical claim — needs a test/spec citation or remove."
require_sourcing_topics:
  - "latency numbers"
  - "compatibility with specific cameras"
  - "throughput / bandwidth figures"
```

`check_claims` runs all regex patterns deterministically with timeout protection (~100ms per pattern) and returns structured hits. Topic-level checks are passed to the host LLM as guidance.

### Why this shape

- **Deterministic where possible** (glossary regex, claims regex) — fast, reliable, fixture-testable.
- **Guidance where nuance is needed** (audience tone, contextual claim validation) — host LLM handles ambiguity.
- **User-editable** — adding a term or banning a phrase = YAML edit, no code change, no release.
- **Versioned** — `version: 1` per file enables future migrations without breaking installs.

## 5. OSP Guidance Bundling & Sync

### 5.1 Approach

OSP's MCP server embeds methodology docs as Python module constants. We extract them into bundled markdown files at build time, kept in sync with upstream via a script. Runtime has zero dependency on the OSP server.

### 5.2 Sync script — `scripts/sync_osp.py`

1. `git clone --depth 1 https://github.com/open-strategy-partners/osp_marketing_tools /tmp/osp-upstream`
2. Extract guidance strings from upstream Python modules (parse with `ast` or import directly).
3. Write each guide to `resources/osp/<name>.md`.
4. Record upstream commit SHA in `resources/osp/.source-sha`.
5. Update `resources/osp/ATTRIBUTION.md` with date, SHA, and CC BY-SA 4.0 notice.
6. Run the test suite to catch format drift before committing.

Manual run: `uv run scripts/sync_osp.py`. Bundled files ship in the wheel — sync is **not** part of install.

### 5.3 CI sync workflow — `.github/workflows/sync-osp.yml`

Weekly cron job runs `sync_osp.py`. If upstream commit SHA changed, opens a PR with the updated bundled files. Human review and merge.

### 5.4 Attribution — `resources/osp/ATTRIBUTION.md`

```
OSP guidance documents in this directory are derived from:
  https://github.com/open-strategy-partners/osp_marketing_tools
  Commit: <sha>  Synced: <date>
  License: CC BY-SA 4.0

Per CC BY-SA 4.0, this project (cyanview-osp-writer) distributes
modified and unmodified excerpts of OSP materials under the same license.
```

### 5.5 License decision

The whole `cyanview-osp-writer` package is licensed **CC BY-SA 4.0** to match upstream OSP. Cyanview-specific layers (`resources/cyanview/*`) are covered by the same license. This avoids dual-licensing complexity.

### 5.6 Runtime serving

`resources.py` reads all bundled files once at startup, validates them with pydantic, and caches them in memory. Tools that need guidance text pull from the same cache. MCP `resources/read` requests serve from the cache.

### 5.7 Why not chain the OSP MCP server at runtime

- OSP's guidance is static documentation, not a live service.
- Chaining adds child-process management and failure modes for zero benefit.
- Bundling enables offline operation, deterministic tests, and controlled update timing.

## 6. Error Handling

Three explicit boundaries. Trust internals between them.

### 6.1 Tool input validation (MCP boundary)

- Every tool's input schema is a `pydantic` model. Invalid calls fail before reaching tool logic, with clear errors returned to the host.
- `audience` and `content_type` are `Literal[...]` enums — typo'd values fail fast with the allowed list in the error message.
- `text` has a max length (~50k chars). Longer input returns a `text_too_long` error suggesting `review_draft` be called per section.

### 6.2 Resource loading (startup boundary)

- On server start, `resources.py` validates all bundled YAML and markdown files exist and parse correctly.
- YAML files validated against pydantic schemas (one model per file) at load time.
- Any missing or malformed file → server **fails to start** with a clear stderr message. Better to never start than to serve a half-broken tool.

### 6.3 Regex execution (layer boundary)

- All regex patterns from `claims-patterns.yaml` and `glossary.yaml` are compiled at startup. Bad regex fails server startup, not first request.
- Regex matches use the `regex` package's `timeout=` argument (~100ms per pattern) to defend against catastrophic backtracking from future YAML edits.

### 6.4 Logging

Structured stderr logging via `structlog`. One log line per tool call: tool name, audience, content_type, text length. **Draft text is never logged** — drafts may be confidential.

### 6.5 No runtime fallbacks for OSP upstream

There is no upstream at runtime. Files are bundled. A missing bundled file is a build/release bug, not a runtime concern.

## 7. Testing

Stack: `pytest`, `pytest-asyncio`, `pytest-cov`, the `mcp` SDK's in-process test client. Target: **80%+ coverage**, TDD methodology.

### 7.1 Unit tests — `tests/layers/`

- `test_glossary.py` — fixture drafts with rejected terms → assert hits with correct offsets and canonical suggestions. Edge cases: term inside code block, term as substring of another word, case sensitivity.
- `test_claims.py` — fixture drafts with each banned pattern → assert detection. Negative cases: superlative inside a quote attribution.
- `test_audience.py` — pure prompt-assembly test (no LLM): given draft + audience, assert output guidance contains the right profile and the draft.

### 7.2 Tool tests — `tests/tools/`

In-process MCP client.

- `test_review_draft.py` — call orchestrator with a known draft, assert returned brief has all expected sections in order, contains glossary hits, contains OSP editing-codes guidance text, contains audience profile.
- One test per sub-tool: input → expected structured output shape.

### 7.3 Integration tests — `tests/integration/`

- `test_server_startup.py` — server starts, lists tools, lists resources, all bundled files served correctly.
- `test_resource_validation.py` — every bundled YAML passes its pydantic schema; every bundled OSP markdown is non-empty and contains expected section headers (catches sync drift).
- `test_sync_script.py` — runs `sync_osp.py` against a frozen test fixture (cached upstream tarball, not network) — proves sync logic survives upstream refactors.

### 7.4 Fixtures — `tests/fixtures/`

- `drafts/` — small markdown files: clean draft, glossary-violations, claims-violations, mixed-violations, draft-with-code-blocks.
- `osp-snapshot/` — frozen copy of OSP upstream for sync-script tests.

### 7.5 No LLM in tests

We test that tools return the right prompts and structured data. Host-LLM review behavior is not our test surface — that's a manual validation step (run against 3-5 real Cyanview drafts before each release).

### 7.6 CI

GitHub Actions runs `uv run pytest --cov=src --cov-fail-under=80` on every push and PR. Weekly cron runs `sync_osp.py` and opens a PR on drift.

## 8. Project Layout

```
cyanview-osp-writer/
├── pyproject.toml
├── README.md
├── LICENSE                       # CC BY-SA 4.0
├── ATTRIBUTION.md                # OSP credit, root level
├── .github/workflows/
│   ├── test.yml                  # pytest on push/PR
│   └── sync-osp.yml              # weekly OSP sync → PR
├── scripts/
│   └── sync_osp.py
├── src/cyanview_osp_writer/
│   ├── __init__.py
│   ├── __main__.py               # `python -m cyanview_osp_writer`
│   ├── server.py                 # MCP server bootstrap
│   ├── resources.py              # bundled-file loader/cache
│   ├── schemas.py                # pydantic models for YAML files
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── review_draft.py       # orchestrator
│   │   ├── osp_edit.py
│   │   ├── osp_seo.py
│   │   ├── osp_meta.py
│   │   ├── check_glossary.py
│   │   ├── check_audience.py
│   │   └── check_claims.py
│   ├── layers/
│   │   ├── glossary.py           # regex engine + hit model
│   │   ├── audience.py           # profile lookup + prompt assembly
│   │   └── claims.py             # regex engine + hit model
│   └── resources/
│       ├── osp/                  # bundled OSP guidance (synced)
│       │   ├── writing-guide.md
│       │   ├── editing-codes.md
│       │   ├── seo-guide.md
│       │   ├── meta-guide.md
│       │   ├── value-map.md
│       │   ├── ATTRIBUTION.md
│       │   └── .source-sha
│       └── cyanview/
│           ├── glossary.yaml
│           ├── audiences.yaml
│           └── claims-patterns.yaml
└── tests/
    ├── conftest.py
    ├── fixtures/
    │   ├── drafts/
    │   └── osp-snapshot/
    ├── layers/
    ├── tools/
    └── integration/
```

Files stay 200-400 lines, 800 max. One tool per file, one layer per file, one schema model per YAML resource type. Adding a new sub-tool = one file in `tools/` + one entry in `server.py`'s tool registry.

## 9. Packaging

### 9.1 `pyproject.toml`

```toml
[project]
name = "cyanview-osp-writer"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "mcp>=1.0",
  "pydantic>=2.0",
  "pyyaml>=6.0",
  "structlog>=24.0",
  "regex>=2024.0",        # supports timeout=
]

[project.scripts]
cyanview-osp-writer = "cyanview_osp_writer.__main__:main"

[tool.hatch.build.targets.wheel]
packages = ["src/cyanview_osp_writer"]
include = ["src/cyanview_osp_writer/resources/**/*"]

[dependency-groups]
dev = ["pytest", "pytest-asyncio", "pytest-cov", "ruff"]
```

Bundled resources are package data shipped inside the wheel, accessed via `importlib.resources`.

### 9.2 Install (Claude Code MCP config)

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

Mirrors the existing `osp_marketing_tools` install ergonomics. No credentials, no environment variables. Pin to a tag (`@v0.1.0`) once releases are cut.

## 10. Day-to-Day Usage (MVP)

1. In Claude Code, paste a Cyanview draft into chat.
2. Ask: *"Review this draft for a broadcast engineer audience."*
3. Claude calls `review_draft(text=..., audience="broadcast_engineer", content_type="blog_post")`.
4. The tool returns the structured `ReviewBrief`.
5. Claude executes the brief against the draft and renders the review inline: glossary hits, OSP editing-codes pass, audience tone notes, claims flags, SEO suggestions, meta block.
6. You iterate. Re-run individual sub-tools (`check_claims`, `osp_seo`) on revisions without redoing the full pipeline.

## 11. Phase 2 Extension Points

Architecture deliberately supports the following without rework:

- `draft_new(brief)` — drafting mode. New tool file in `tools/`. Uses `osp://value-map.md` to walk through positioning, then composes a draft from user-supplied product/audience inputs, then runs `review_draft` on the result.
- `review_odoo_article(article_id)` — fetches from existing Cyanview Odoo MCP, reviews, optionally writes back. New tool file plus a thin Odoo client wrapper.
- `review_file(path)` — local markdown review. New tool file. Path safety check (must be under a configured workspace root).
- Claude Desktop MCP App UI — same server, new front-end. Tool surface unchanged.

Each extension is one new file in `tools/` plus a registry entry. Layers, resources, error model, and packaging are unchanged.

## 12. Open Items for Implementation Phase

- Seed ~20 glossary terms (collected from Cyanview website, recent product pages, and existing docs).
- Confirm exact `regex` package version supporting `timeout=`.
- Decide whether `mixed` audience is MVP or Phase 2 (current design includes it; could cut to ship faster).
- README content and quickstart examples.

---

**End of design spec.** Implementation plan to be created via the `superpowers:writing-plans` skill after user review of this document.
