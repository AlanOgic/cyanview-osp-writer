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
from datetime import UTC, datetime
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
