# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`cyanview-osp-writer` is a Cyanview-flavoured fork of the upstream Open Strategy Partners [`osp_marketing_tools`](https://github.com/open-strategy-partners/osp_marketing_tools) MCP server. It re-exposes the five OSP guide tools (writing, editing, SEO, meta, value-map) and adds Cyanview-specific layers (glossary, claims, audience) plus an orchestrator (`review_draft`) that bundles the relevant pieces into a single review brief. Local stdio MCP server distributed via `uvx` — no credentials, no env vars.

## Commands

```bash
uv sync                                                      # install deps incl. dev
uv run pytest                                                # full test suite
uv run pytest --cov=src --cov-report=term-missing            # with coverage (gated at 80%)
uv run pytest tests/tools/test_check_glossary.py             # single file
uv run pytest tests/tools/test_check_glossary.py::test_name  # single test
uv run ruff check src tests                                  # lint
uv run ruff check --fix src tests                            # lint + autofix
uv run python scripts/sync_osp.py                            # refresh OSP guidance from upstream
uv run python scripts/sync_osp.py --from /path/to/clone      # sync from a local clone (for tests)
uv run cyanview-osp-writer                                   # run the MCP server over stdio
```

CI (`.github/workflows/test.yml`) runs ruff + pytest with `--cov-fail-under=80` on Python 3.11 and 3.12. The `sync-osp.yml` workflow is manual-only (`workflow_dispatch`) — trigger from the Actions tab to run `scripts/sync_osp.py` and open a PR if upstream OSP guidance changed.

## Architecture

The server is a thin wrapper around six review primitives. Each primitive is split into three layers so the deterministic logic stays testable in isolation from the MCP transport:

```
server.py (FastMCP)        ── registers tools + resources
  └─ tools/<name>.py       ── tool entry point: validates input, loads resources, returns Pydantic model
       └─ layers/<name>.py ── pure logic (regex engine, prompt assembler) — no I/O, no MCP
            └─ schemas.py  ── Pydantic models for bundled YAML resources
```

### Tool surface

**Cyanview brand layers (deterministic):**
1. **`check_glossary_tool`** — regex against `resources/cyanview/glossary.yaml`. Skips fenced code blocks via offset-preserving masking in `layers/glossary.py`.
2. **`check_claims_tool`** — regex against `resources/cyanview/claims-patterns.yaml` (banned superlatives + technical claims needing sources).
3. **`check_audience_tool`** — assembles a tone/vocabulary review prompt from `resources/cyanview/audiences.yaml`. Does NOT call an LLM — the host (Claude Code) executes the assembled prompt.

**OSP guide tools (parity with upstream `osp_marketing_tools`):**
4. **`osp_edit_tool`** / **`osp_seo_tool`** / **`osp_meta_tool`** / **`osp_writing_tool`** / **`osp_value_map_tool`** — return bundled OSP guide markdown alongside the draft, in a `GuidanceResult` envelope with a `source` field (e.g. `osp:editing-codes`). The host LLM does the semantic review.

**Cyanview orchestrator:**
5. **`review_draft_tool`** — validates `audience` + `content_type` + optional `focus` subset, runs each requested layer (glossary, claims, audience, edit, seo, meta — *not* writing or value-map), packages everything into a `ReviewBrief` with an `execution_plan` telling the host LLM how to render the review.

All tools enforce `MAX_TEXT_CHARS = 50_000` and raise `ValueError` with a `<reason>: <detail>` message on bad input. Regex layers use `regex.finditer(..., timeout=0.1)` to bound runtime.

### Resources

Resources are bundled into the wheel via `[tool.hatch.build.targets.wheel.force-include]` — they MUST ship with the package since `uvx` installs from the wheel without source tree access.

- `resources/cyanview/*.yaml` — Cyanview-authored brand layers (glossary, audiences, claims). Validated by Pydantic schemas in `schemas.py` with `extra="forbid"`. The audiences schema requires exactly the three keys in `REQUIRED_AUDIENCES = {"dp", "broadcast_engineer", "rental_house"}`.
- `resources/osp/*.md` — synced from upstream OSP repo. Never edit by hand; run `scripts/sync_osp.py`. The upstream commit SHA is recorded in `resources/osp/.source-sha` and surfaced in every `ReviewBrief` so reviews are reproducible.

`resources.py::load_resources()` is `@lru_cache(maxsize=1)` — the cache is the single source of truth for the running server. Tests that mutate bundled files must call `resources.reset_cache()`.

The same files are exposed as MCP resources at `cyanview://glossary.yaml`, `cyanview://audiences.yaml`, `cyanview://claims-patterns.yaml`, and `osp://<guide>.md` for the five guides listed in `OSP_GUIDE_NAMES`.

### Sync script

`scripts/sync_osp.py` clones the upstream OSP repo, dynamically imports `src/osp_marketing_tools/server.py`, and reads module-level string constants (`WRITING_GUIDE`, `EDITING_CODES`, etc.) listed in `GUIDE_MAP`. Each guide is written to `resources/osp/<name>.md` with the SHA recorded in `.source-sha` and `ATTRIBUTION.md`. **If upstream renames a constant, update `GUIDE_MAP`** — the script will fail loudly with a "update GUIDE_MAP" message rather than silently produce stale output.

### Determinism boundary

The deterministic regex layers (glossary, claims) detect issues. The OSP layers (`osp_edit`, `osp_seo`, `osp_meta`) and the audience layer assemble guidance + draft for the host LLM to interpret. **The MCP server itself never calls an LLM.** This is intentional — keeps the server pure, fast, and testable.

## Conventions specific to this project

- All output models are Pydantic with `model_config = ConfigDict(extra="forbid")`. Tools return `.model_dump()` from the FastMCP wrapper so MCP clients get plain dicts.
- The audience taxonomy is planned to change in v0.2.0 (3 → 4 audiences: `vision_engineer`, `integrator`, `end_user`, `renter_reseller`), deferred until real-draft usage informs the profiles. When changing audiences: edit `audiences.yaml`, `schemas.py::REQUIRED_AUDIENCES`, `VALID_AUDIENCES` in `tools/check_audience.py` and `tools/review_draft.py`, the mixed branch in `layers/audience.py`, and the corresponding tests.
- Logs go to stderr as JSON via `structlog`. Never write to stdout — stdout is the MCP transport.
- License is CC BY-SA 4.0 (because OSP upstream is). New files in `resources/cyanview/` are also CC BY-SA 4.0.
