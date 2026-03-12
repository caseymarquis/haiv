"""Tests for haiv.helpers.chart module."""

import pytest
from pathlib import Path

from haiv.helpers.chart import (
    ensure_atlas_structure,
    ensure_example_journey,
    get_briefing,
    load_exploration,
    save_exploration,
    clear_exploration,
    show_status,
)
from haiv.paths import AtlasPaths, MindPaths
from haiv.templates import TemplateRenderer


@pytest.fixture
def atlas(tmp_path) -> AtlasPaths:
    """An atlas rooted in a temp directory."""
    return AtlasPaths(root=tmp_path / "atlas")


@pytest.fixture
def mind(tmp_path) -> MindPaths:
    """A mind with work directory in a temp directory."""
    mind = MindPaths(root=tmp_path / "minds" / "pixel")
    mind.work.root.mkdir(parents=True)
    return mind


@pytest.fixture
def bundled_dir(tmp_path) -> Path:
    """A fake bundled example journey directory."""
    d = tmp_path / "bundled" / "example-journey"
    d.mkdir(parents=True)
    (d / "001-research-log.md").write_text("# Research Log\n")
    (d / "002-some-entry.md").write_text("# Some Entry\n")
    (d / "not-markdown.txt").write_text("ignored\n")
    return d


# =============================================================================
# Atlas structure
# =============================================================================


class TestEnsureAtlasStructure:
    def test_creates_all_directories(self, atlas: AtlasPaths):
        ensure_atlas_structure(atlas)

        assert atlas.journeys_dir.is_dir()
        assert atlas.maps_dir.is_dir()
        assert atlas.examples_dir.is_dir()

    def test_idempotent(self, atlas: AtlasPaths):
        ensure_atlas_structure(atlas)
        ensure_atlas_structure(atlas)

        assert atlas.journeys_dir.is_dir()


# =============================================================================
# Example journeys
# =============================================================================


class TestEnsureExampleJourney:
    def test_copies_bundled_when_empty(self, atlas: AtlasPaths, bundled_dir: Path):
        ensure_atlas_structure(atlas)
        files = ensure_example_journey(atlas, bundled_dir)

        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)
        assert files[0].name == "001-research-log.md"
        assert files[1].name == "002-some-entry.md"

    def test_copies_only_files(self, atlas: AtlasPaths, bundled_dir: Path):
        """Subdirectories in bundled dir are not copied."""
        (bundled_dir / "subdir").mkdir()
        ensure_atlas_structure(atlas)
        files = ensure_example_journey(atlas, bundled_dir)

        assert not (atlas.examples_dir / "subdir").exists()
        assert len(files) == 2

    def test_filters_to_markdown_only(self, atlas: AtlasPaths, bundled_dir: Path):
        """Only .md files are returned, even if other files are copied."""
        ensure_atlas_structure(atlas)
        files = ensure_example_journey(atlas, bundled_dir)

        names = [f.name for f in files]
        assert "not-markdown.txt" not in names

    def test_preserves_existing_content(self, atlas: AtlasPaths, bundled_dir: Path):
        ensure_atlas_structure(atlas)
        custom = atlas.examples_dir / "my-example.md"
        custom.write_text("# Custom\n")

        files = ensure_example_journey(atlas, bundled_dir)

        names = [f.name for f in files]
        assert "my-example.md" in names
        assert "001-research-log.md" not in names

    def test_returns_empty_when_no_bundled(self, atlas: AtlasPaths, tmp_path: Path):
        nonexistent = tmp_path / "does-not-exist"
        files = ensure_example_journey(atlas, nonexistent)

        assert files == []

    def test_creates_examples_dir_if_missing(self, atlas: AtlasPaths, bundled_dir: Path):
        """Does not require ensure_atlas_structure to be called first."""
        files = ensure_example_journey(atlas, bundled_dir)

        assert atlas.examples_dir.is_dir()
        assert len(files) == 2


# =============================================================================
# Exploration state
# =============================================================================


class TestExplorationState:
    def test_load_returns_none_when_no_state(self, mind: MindPaths):
        assert load_exploration(mind) is None

    def test_save_and_load_roundtrip(self, mind: MindPaths):
        state = {"journey": "test", "status": "new", "entry": 1}
        save_exploration(mind, state)
        loaded = load_exploration(mind)

        assert loaded == state

    def test_clear_removes_state(self, mind: MindPaths):
        save_exploration(mind, {"journey": "test", "status": "new"})
        clear_exploration(mind)

        assert load_exploration(mind) is None

    def test_clear_idempotent(self, mind: MindPaths):
        clear_exploration(mind)
        assert load_exploration(mind) is None


# =============================================================================
# Show status
# =============================================================================


class TestShowStatus:
    def test_shows_journey_name(self):
        output = show_status({"journey": "my-quest", "entry": 3, "status": "planned"})
        assert "my-quest" in output

    def test_shows_entry_number(self):
        output = show_status({"journey": "test", "entry": 5, "status": "reflected"})
        assert "005" in output

    def test_shows_destination_when_embarked(self):
        output = show_status({
            "journey": "test", "entry": 2, "status": "embarked",
            "destination": "src/haiv/cmd.py",
        })
        assert "src/haiv/cmd.py" in output

    def test_shows_next_step_guidance(self):
        output = show_status({"journey": "test", "entry": 1, "status": "new"})
        assert "--log" in output
