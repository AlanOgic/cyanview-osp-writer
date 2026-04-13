"""Integration: sync_osp script runs against a frozen snapshot fixture."""

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIR = PROJECT_ROOT / "tests" / "fixtures" / "osp_snapshot"


@pytest.mark.skipif(
    not (SNAPSHOT_DIR / "src" / "osp_marketing_tools" / "server.py").exists(),
    reason=(
        "OSP snapshot fixture not yet captured "
        "(see tests/fixtures/osp_snapshot/README.md)"
    ),
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
    guide_names = (
        "writing-guide",
        "editing-codes",
        "seo-guide",
        "meta-guide",
        "value-map",
    )
    for name in guide_names:
        f = osp_dir / f"{name}.md"
        assert f.exists()
        assert f.read_text().strip()
    sha = (osp_dir / ".source-sha").read_text().strip()
    assert len(sha) == 40
