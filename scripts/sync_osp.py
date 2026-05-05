"""Sync OSP upstream guidance into bundled markdown resources.

Strategy:
1. Clone upstream into a temp dir (or use a local snapshot path).
2. Parse upstream Python modules with ``ast.parse`` (no execution) and
   extract top-level string-constant assignments by name.
3. Write each guide to src/cyanview_osp_writer/resources/osp/<name>.md.
4. Record the upstream commit SHA in .source-sha.
5. Update ATTRIBUTION.md with the sync date and SHA.

Mapping from upstream constant names to our guide files is defined in
GUIDE_MAP. If upstream renames a constant or switches to non-literal
values (concatenation, f-strings, function calls), the script fails
loudly with an "update GUIDE_MAP" message — update the map and, if
needed, extend ``_parse_string_constants`` to handle the new shape.
"""

from __future__ import annotations

import argparse
import ast
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


def _parse_string_constants(module_path: Path) -> dict[str, str]:
    """Parse a Python module and extract top-level string-constant assignments.

    Walks the AST without executing the module. Recognises the form
    ``NAME = "..."`` where the value is a single ``ast.Constant`` of type
    ``str``. Skips any other shape (function calls, concatenations,
    f-strings with substitutions, etc.) — upstream guidance modules use
    plain triple-quoted literals, so this is sufficient.

    Returns a dict mapping name → string value. Names not matching the
    expected shape are simply absent from the result; callers should
    check membership and raise a structured error if a required name
    is missing.
    """
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(module_path))
    out: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not (
            isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        ):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                out[target.id] = node.value.value
    return out


def _extract(clone_root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    parsed: dict[str, dict[str, str]] = {}
    for (rel_path, const_name), guide_name in GUIDE_MAP.items():
        if rel_path not in parsed:
            module_path = clone_root / rel_path
            if not module_path.exists():
                raise RuntimeError(
                    f"Expected upstream module not found: {module_path}. "
                    f"Update GUIDE_MAP in scripts/sync_osp.py."
                )
            parsed[rel_path] = _parse_string_constants(module_path)
        constants = parsed[rel_path]
        if const_name not in constants:
            raise RuntimeError(
                f"Upstream module {rel_path} does not define {const_name} "
                f"as a top-level string literal. "
                f"Update GUIDE_MAP in scripts/sync_osp.py."
            )
        out[guide_name] = constants[const_name]
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
