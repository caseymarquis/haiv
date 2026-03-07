"""Tests for hv become command."""

import os
import pytest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from haiv import test
from haiv._infrastructure.args import ResolveRequest
from haiv.errors import CommandError

from haiv.helpers.minds import Mind, MindPaths


class TestBecomeRouting:
    """Test that 'become {mind}' routes correctly."""

    def test_routes_to_mind_file(self):
        """'become wren' routes to become/_mind_.py."""
        match = test.require_routes_to("become wren")
        assert match.file.name == "_mind_.py"
        assert "become" in str(match.file)

    def test_captures_mind_param(self):
        """Mind name is captured as param."""
        match = test.require_routes_to("become wren")
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
    """Test HV_MIND environment variable handling."""

    def test_prints_bootstrap_when_haiv_mind_not_set(self, tmp_path, capsys):
        """When HV_MIND is not set, prints bootstrap instructions."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HV_MIND", None)
            test.execute("become wren", resolve=mock_resolve)

        captured = capsys.readouterr()
        assert "HV_MIND is not set" in captured.out
        assert "export HV_MIND=wren" in captured.out
        assert "hv become wren" in captured.out

    def test_errors_when_different_mind(self, tmp_path):
        """When HV_MIND is set to a different mind, raises error."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir))

        with patch.dict(os.environ, {"HV_MIND": "robin"}):
            with pytest.raises(CommandError) as exc_info:
                test.execute("become wren", resolve=mock_resolve)

            assert "Already running as 'robin'" in str(exc_info.value)
            assert "Cannot become 'wren'" in str(exc_info.value)

    def test_outputs_files_when_haiv_mind_matches(self, tmp_path, capsys):
        """When HV_MIND matches, outputs files to read."""
        mind_dir = tmp_path / "wren"
        work_dir = mind_dir / "work"
        work_dir.mkdir(parents=True)
        (mind_dir / "references.toml").write_text("")
        (work_dir / "identity.md").write_text("# Identity")

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir, haiv_root=tmp_path))

        def setup(ctx):
            ctx.paths._haiv_root = tmp_path

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "Welcome back, wren!" in captured.out
        assert "documents you left for yourself" in captured.out
        assert "identity.md" in captured.out


class TestBecomeExecution:
    """Test become command file output."""

    def test_outputs_references_from_toml(self, tmp_path, capsys):
        """Outputs paths from references.toml."""
        haiv_root = tmp_path
        def mock_resolve(req: ResolveRequest) -> Mind:
            return _create_mock_mind(
                req.value,
                haiv_root=haiv_root,
                startup_files=[
                    haiv_root / "src/roles/coo.md",
                    haiv_root / "docs/problems.md",
                ],
            )

        def setup(ctx):
            ctx.paths._haiv_root = haiv_root

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "Welcome back, wren!" in captured.out
        assert "documents you left for yourself" in captured.out
        assert "src/roles/coo.md" in captured.out
        assert "docs/problems.md" in captured.out

    def test_outputs_work_files(self, tmp_path, capsys):
        """Outputs files from work/ directory."""
        mind_dir = tmp_path / "wren"
        work_dir = mind_dir / "work"
        work_dir.mkdir(parents=True)
        (mind_dir / "references.toml").write_text("")
        (work_dir / "identity.md").write_text("# Identity")
        (work_dir / "current-focus.md").write_text("# Focus")

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir, haiv_root=tmp_path))

        def setup(ctx):
            ctx.paths._haiv_root = tmp_path

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "Welcome back, wren!" in captured.out
        assert "documents you left for yourself" in captured.out
        assert "identity.md" in captured.out
        assert "current-focus.md" in captured.out
        assert "references.toml" not in captured.out

    def test_outputs_files_sorted_by_name(self, tmp_path, capsys):
        """All files are sorted by name in output."""
        haiv_root = tmp_path
        def mock_resolve(req: ResolveRequest) -> Mind:
            return _create_mock_mind(
                req.value,
                haiv_root=haiv_root,
                startup_files=[
                    haiv_root / "wren/work/zebra.md",
                    haiv_root / "wren/work/alpha.md",
                ],
            )

        def setup(ctx):
            ctx.paths._haiv_root = haiv_root

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        alpha_pos = next(i for i, l in enumerate(lines) if "alpha.md" in l)
        zebra_pos = next(i for i, l in enumerate(lines) if "zebra.md" in l)
        assert alpha_pos < zebra_pos

    def test_empty_mind_shows_message(self, tmp_path, capsys):
        """Shows message when mind has no files."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir(parents=True)
        (mind_dir / "references.toml").write_text("")

        def mock_resolve(req: ResolveRequest) -> Mind:
            return Mind(paths=MindPaths(root=mind_dir, haiv_root=tmp_path))

        def setup(ctx):
            ctx.paths._haiv_root = tmp_path

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("become wren", resolve=mock_resolve, setup=setup)

        captured = capsys.readouterr()
        assert "Welcome back, wren!" in captured.out
        assert "no startup documents" in captured.out


def _create_mock_mind(
    name: str,
    haiv_root: Path,
    startup_files: list[Path] | None = None,
) -> Mind:
    """Create a Mind with mocked get_startup_files.

    Args:
        name: Mind name.
        haiv_root: The haiv root path (needed for MindPaths).
        startup_files: List of absolute Paths to return from get_startup_files().
    """

    class MockMind(Mind):
        def __init__(self, name: str, haiv_root: Path, files: list[Path]):
            super().__init__(paths=MindPaths(root=Path(f"/fake/minds/{name}"), haiv_root=haiv_root))
            self._files = files

        def get_startup_files(self) -> list[Path]:
            return sorted(self._files, key=lambda p: p.name)

    return MockMind(name, haiv_root, startup_files or [])
