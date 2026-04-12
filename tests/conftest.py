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
