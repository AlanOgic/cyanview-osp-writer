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

The full set of upstream OSP guides is available as standalone tools too —
`osp_writing_tool` (writing guide) and `osp_value_map_tool` (value map) — for
parity with `osp_marketing_tools`. They aren't part of the Cyanview review
pipeline but can be called directly when you want their guidance.

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
