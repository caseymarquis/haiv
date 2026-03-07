"""Tests for hv mine command."""

import os
import pytest
from unittest.mock import patch

from haiv import test
from haiv.errors import CommandError

from haiv.helpers.minds import Mind, MindPaths


def create_mind(ctx, name: str, role: str | None = None) -> Mind:
    """Helper to create a mind using ctx.paths."""
    ctx.paths.user.minds_dir.mkdir(parents=True, exist_ok=True)
    mind = Mind(paths=MindPaths(root=ctx.paths.user.minds_dir / name, hv_root=ctx.paths.root))
    mind.ensure_structure()
    if role:
        mind.paths.references_file.write_text(f'role = "{role}"\n')
    return mind


class TestMineRouting:
    """Test that 'mine' routes correctly."""

    def test_routes_to_mine_file(self):
        """'mine' routes to mine.py."""
        match = test.require_routes_to("mine")
        assert match.file.name == "mine.py"


class TestMineExecution:
    """Test mine command execution."""

    def test_requires_hv_mind_env_var(self):
        """mine fails without HV_MIND environment variable."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("HV_MIND", None)

            with pytest.raises(CommandError) as exc_info:
                test.execute("mine")

            assert "HV_MIND" in str(exc_info.value)

    def test_outputs_mind_name_and_location(self, capsys):
        """mine outputs mind name and location."""
        def setup(ctx):
            create_mind(ctx, "wren")

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("mine", setup=setup)

        captured = capsys.readouterr()
        assert "wren" in captured.out
        assert "minds/wren" in captured.out

    def test_outputs_work_path(self, capsys):
        """mine outputs work directory path."""
        def setup(ctx):
            create_mind(ctx, "wren")

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("mine", setup=setup)

        captured = capsys.readouterr()
        assert "work" in captured.out.lower()

    def test_outputs_role_from_references(self, capsys):
        """mine outputs role if present in references.toml."""
        def setup(ctx):
            create_mind(ctx, "wren", role="Software Engineer")

        with patch.dict(os.environ, {"HV_MIND": "wren"}):
            test.execute("mine", setup=setup)

        captured = capsys.readouterr()
        assert "Software Engineer" in captured.out

    def test_handles_missing_mind_gracefully(self):
        """mine provides helpful error for non-existent mind."""
        def setup(ctx):
            ctx.paths.user.minds_dir.mkdir(parents=True, exist_ok=True)

        with patch.dict(os.environ, {"HV_MIND": "nonexistent"}):
            with pytest.raises(Exception):  # MindNotFoundError
                test.execute("mine", setup=setup)
