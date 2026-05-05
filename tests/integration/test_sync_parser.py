"""Unit tests for sync_osp._parse_string_constants.

The full sync-script integration test (test_sync_script.py) is skipped
when the OSP snapshot fixture is absent. These tests cover the AST
parser in isolation so the parsing logic stays under test regardless.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import sync_osp  # noqa: E402


class TestParseStringConstants:
    def test_extracts_simple_assignment(self, tmp_path: Path):
        module = tmp_path / "fake.py"
        module.write_text('FOO = "hello"\nBAR = "world"\n', encoding="utf-8")
        result = sync_osp._parse_string_constants(module)
        assert result == {"FOO": "hello", "BAR": "world"}

    def test_extracts_triple_quoted(self, tmp_path: Path):
        module = tmp_path / "fake.py"
        module.write_text(
            'GUIDE = """# Heading\n\nBody text.\n"""\n', encoding="utf-8"
        )
        result = sync_osp._parse_string_constants(module)
        assert result == {"GUIDE": "# Heading\n\nBody text.\n"}

    def test_skips_non_string_values(self, tmp_path: Path):
        module = tmp_path / "fake.py"
        module.write_text(
            'NUMBER = 42\nLIST = [1, 2, 3]\nGREETING = "hi"\n',
            encoding="utf-8",
        )
        result = sync_osp._parse_string_constants(module)
        assert result == {"GREETING": "hi"}

    def test_skips_concatenation_and_calls(self, tmp_path: Path):
        # ast.Constant matches only single literals; concatenation and
        # function calls are intentionally skipped so the failure mode
        # is "missing constant", not "wrong content".
        module = tmp_path / "fake.py"
        module.write_text(
            'CONCAT = "a" + "b"\nCALL = str("x")\nSIMPLE = "kept"\n',
            encoding="utf-8",
        )
        result = sync_osp._parse_string_constants(module)
        assert result == {"SIMPLE": "kept"}

    def test_does_not_execute_module(self, tmp_path: Path):
        # If the parser executed the module, this would raise.
        module = tmp_path / "fake.py"
        module.write_text(
            'GUIDE = "safe"\nraise RuntimeError("module-level side effect")\n',
            encoding="utf-8",
        )
        # Should parse cleanly — the raise is never executed.
        result = sync_osp._parse_string_constants(module)
        assert result == {"GUIDE": "safe"}

    def test_ignores_imports_and_classes(self, tmp_path: Path):
        module = tmp_path / "fake.py"
        module.write_text(
            'import os\n\nclass C:\n    X = "nested"\n\nTOP = "kept"\n',
            encoding="utf-8",
        )
        result = sync_osp._parse_string_constants(module)
        assert result == {"TOP": "kept"}
