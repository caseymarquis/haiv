"""Tests for mg become command."""

import os
import pytest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from mg import test
from mg.args import ResolveRequest
from mg.errors import CommandError

from mg_core.helpers.minds import Mind, MindPaths


class TestBecomeRouting:
    """Test that 'become {mind}' routes correctly."""

    def test_routes_to_mind_file(self):
        """'become wren' routes to become/_mind_.py."""
        match = test.routes_to("become wren")
        assert match.file.name == "_mind_.py"
        assert "become" in str(match.file)

    def test_captures_mind_param(self):
        """Mind name is captured as param."""
        match = test.routes_to("become wren")
        assert "mind" in match.params
        assert match.params["mind"].value == "wren"
        assert match.params["mind"].resolver == "mind"


class TestBecomeParsing:
    """Test become command argument parsing."""

    def test_parses_mind_name(self):
        """Mind name is accessible via args."""
        def mock_resolve(req: ResolveRequest) -> Any:
            return req.value  # Return raw value for parsing test

        ctx = test.parse("become wren", resolve=mock_resolve)
        assert ctx.args.get_one("mind") == "wren"


class TestBecomeEnvironmentChecks:
    """Test MG_MIND environment variable handling."""

    def test_prints_bootstrap_when_mg_mind_not_set(self, tmp_path, capsys):
        """When MG_MIND is not set, prints bootstrap instructions."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MG_MIND", None)
            test.execute("become wren", resolve=mock_resolve)

        captured = capsys.readouterr()
        assert "MG_MIND is not set" in captured.out
        assert "export MG_MIND=wren" in captured.out
        assert "mg become wren" in captured.out

    def test_errors_when_different_mind(self, tmp_path):
        """When MG_MIND is set to a different mind, raises error."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        with patch.dict(os.environ, {"MG_MIND": "robin"}):
            with pytest.raises(CommandError) as exc_info:
                test.execute("become wren", resolve=mock_resolve)

            assert "Already running as 'robin'" in str(exc_info.value)
            assert "Cannot become 'wren'" in str(exc_info.value)

    def test_outputs_files_when_mg_mind_matches(self, tmp_path, capsys):
        """When MG_MIND matches, outputs files to read."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "references.toml").write_text("")
        (startup_dir / "identity.md").write_text("# Identity")

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch.dict(os.environ, {"MG_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "Read the following files" in captured.out
        assert "identity.md" in captured.out


class TestBecomeExecution:
    """Test become command file output."""

    def test_outputs_references_from_toml(self, capsys):
        """Outputs paths from references.toml."""
        def mock_resolve(req: ResolveRequest) -> Mind:
            return _create_mock_mind(
                req.value,
                references=["src/roles/coo.md", "docs/problems.md"],
            )

        def setup(ctx):
            ctx.paths._mg_root = Path("/fake/root")

        with patch.dict(os.environ, {"MG_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "Read the following files" in captured.out
        assert "src/roles/coo.md" in captured.out
        assert "docs/problems.md" in captured.out

    def test_outputs_startup_files(self, tmp_path, capsys):
        """Outputs non-toml files from startup/."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "references.toml").write_text("")
        (startup_dir / "identity.md").write_text("# Identity")
        (startup_dir / "current-focus.md").write_text("# Focus")

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch.dict(os.environ, {"MG_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "Read the following files" in captured.out
        assert "identity.md" in captured.out
        assert "current-focus.md" in captured.out
        assert "references.toml" not in captured.out

    def test_outputs_references_before_startup_files(self, tmp_path, capsys):
        """References appear before startup files in output."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "references.toml").write_text('''
[[references]]
path = "src/roles/coo.md"
''')
        (startup_dir / "identity.md").write_text("")

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch.dict(os.environ, {"MG_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        ref_pos = next(i for i, l in enumerate(lines) if "src/roles/coo.md" in l)
        startup_pos = next(i for i, l in enumerate(lines) if "identity.md" in l)
        assert ref_pos < startup_pos

    def test_empty_mind_shows_message(self, tmp_path, capsys):
        """Shows message when mind has no startup files."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "references.toml").write_text("")

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        def setup(ctx):
            ctx.paths._mg_root = tmp_path

        with patch.dict(os.environ, {"MG_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "no startup files" in captured.out


def _create_mock_mind(
    name: str,
    references: list[str] | None = None,
) -> Mind:
    """Create a Mind with mocked get_references."""

    class MockMind(Mind):
        def __init__(self, name: str, refs: list[str]):
            super().__init__(paths=MindPaths(root=Path(f"/fake/minds/{name}")))
            self._refs = refs

        def get_references(self) -> list[str]:
            return self._refs

        def get_startup_files(self) -> list[Path]:
            return []

    return MockMind(name, references or [])
