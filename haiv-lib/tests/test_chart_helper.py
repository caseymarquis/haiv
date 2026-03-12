"""Tests for haiv.helpers.chart module."""

import pytest
from pathlib import Path

from haiv.helpers.chart import (
    ensure_atlas_structure,
    ensure_chart_templates,
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


@pytest.fixture
def bundled_templates(tmp_path) -> Path:
    """A fake bundled chart templates directory with .j2 files."""
    d = tmp_path / "bundled" / "chart"
    d.mkdir(parents=True)
    (d / "briefing.md.j2").write_text("Briefing: {{ goal }}\n")
    (d / "explore-start.md.j2").write_text("Start: {{ name }}\n")
    (d / "research-log.md.j2").write_text("Log: {{ mind }}\n")
    # Non-template file should be ignored
    (d / "README.md").write_text("not a template\n")
    # Subdirectory should be ignored
    (d / "example-journey").mkdir()
    (d / "example-journey" / "001.md").write_text("example\n")
    return d


@pytest.fixture
def local_templates(tmp_path) -> Path:
    """A project-local chart templates directory."""
    return tmp_path / "atlas" / "templates" / "chart"


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
# Chart templates
# =============================================================================


class TestEnsureChartTemplates:
    def test_copies_all_templates_when_empty(self, local_templates: Path, bundled_templates: Path):
        ensure_chart_templates(local_templates, bundled_templates)

        assert (local_templates / "briefing.md.j2").exists()
        assert (local_templates / "explore-start.md.j2").exists()
        assert (local_templates / "research-log.md.j2").exists()

    def test_copies_only_j2_files(self, local_templates: Path, bundled_templates: Path):
        """Non-.j2 files and subdirectories are not copied."""
        ensure_chart_templates(local_templates, bundled_templates)

        assert not (local_templates / "README.md").exists()
        assert not (local_templates / "example-journey").exists()

    def test_preserves_existing_templates(self, local_templates: Path, bundled_templates: Path):
        """Existing customized templates are not overwritten."""
        local_templates.mkdir(parents=True)
        (local_templates / "briefing.md.j2").write_text("Custom briefing\n")

        ensure_chart_templates(local_templates, bundled_templates)

        assert (local_templates / "briefing.md.j2").read_text() == "Custom briefing\n"

    def test_copies_missing_files_individually(self, local_templates: Path, bundled_templates: Path):
        """If one template exists but others don't, only missing ones are copied."""
        local_templates.mkdir(parents=True)
        (local_templates / "briefing.md.j2").write_text("Custom briefing\n")

        ensure_chart_templates(local_templates, bundled_templates)

        # Custom file preserved
        assert (local_templates / "briefing.md.j2").read_text() == "Custom briefing\n"
        # Missing files restored from bundled
        assert (local_templates / "explore-start.md.j2").exists()
        assert (local_templates / "research-log.md.j2").exists()

    def test_creates_templates_dir_if_missing(self, local_templates: Path, bundled_templates: Path):
        assert not local_templates.exists()
        ensure_chart_templates(local_templates, bundled_templates)
        assert local_templates.is_dir()

    def test_returns_templates_dir(self, local_templates: Path, bundled_templates: Path):
        result = ensure_chart_templates(local_templates, bundled_templates)
        assert result == local_templates

    def test_handles_missing_bundled_dir(self, local_templates: Path, tmp_path: Path):
        """Gracefully handles a nonexistent bundled directory."""
        nonexistent = tmp_path / "does-not-exist"
        result = ensure_chart_templates(local_templates, nonexistent)

        assert result == local_templates
        assert local_templates.is_dir()

    def test_idempotent(self, local_templates: Path, bundled_templates: Path):
        ensure_chart_templates(local_templates, bundled_templates)
        ensure_chart_templates(local_templates, bundled_templates)

        assert (local_templates / "briefing.md.j2").exists()


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
