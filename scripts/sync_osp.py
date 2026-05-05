"""Sync OSP upstream guidance into bundled markdown resources.

Strategy:
1. Clone upstream into a temp dir (or use a local snapshot path).
2. Copy the guidance markdown files from the upstream package directly.
3. Write each guide to src/cyanview_osp_writer/resources/osp/<name>.md.
4. Record the upstream commit SHA in .source-sha.
5. Update ATTRIBUTION.md with the sync date and SHA.

Mapping from upstream filenames to our guide names is defined in
GUIDE_MAP. If upstream renames a file, restructures the package, or
switches back to inlining guides as Python constants, the script
fails loudly with an "update GUIDE_MAP" message — update the map.

Historical note: prior to upstream commit b66bcc6e (Sep 2025), the
guides lived as module-level string constants in server.py and this
script parsed them via ast.parse. Upstream has since externalised
the guides as standalone .md files, so the script now copies bytes
directly — simpler and removes any code-execution surface.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_URL = "https://github.com/open-strategy-partners/osp_marketing_tools"
DEFAULT_CLONE_DIR = Path("/tmp/osp-upstream")

# Upstream markdown path (relative to clone root) → our guide name.
# If upstream renames a file or moves the package, edit this map.
GUIDE_MAP: dict[str, str] = {
    "src/osp_marketing_tools/guide-llm.md": "writing-guide",
    "src/osp_marketing_tools/codes-llm.md": "editing-codes",
    "src/osp_marketing_tools/on-page-seo-guide.md": "seo-guide",
    "src/osp_marketing_tools/meta-llm.md": "meta-guide",
    "src/osp_marketing_tools/product-value-map-llm.md": "value-map",
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


def _extract(clone_root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel_path, guide_name in GUIDE_MAP.items():
        source_path = clone_root / rel_path
        if not source_path.exists():
            raise RuntimeError(
                f"Expected upstream guide not found: {source_path}. "
                f"Update GUIDE_MAP in scripts/sync_osp.py."
            )
        out[guide_name] = source_path.read_text(encoding="utf-8")
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
    today = datetime.now(UTC).date().isoformat()
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
