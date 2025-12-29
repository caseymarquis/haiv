"""Tests for mg.templates module."""

from pathlib import Path

import pytest

from mg.templates import TemplateRenderer, TemplateNotFoundError


class TestTemplateRenderer:
    """Tests for TemplateRenderer."""

    @pytest.fixture
    def assets_dir(self, tmp_path):
        """Create a temp assets directory with test templates."""
        assets = tmp_path / "__assets__"
        assets.mkdir()
        return assets

    @pytest.fixture
    def renderer(self, assets_dir):
        """Create a TemplateRenderer with test assets."""
        return TemplateRenderer(assets_dir)

    def test_render_returns_string(self, renderer, assets_dir):
        """render() returns a string."""
        template = assets_dir / "test.txt.j2"
        template.write_text("Hello")

        result = renderer.render("test.txt.j2")

        assert isinstance(result, str)
        assert result == "Hello"

    def test_render_substitutes_variables(self, renderer, assets_dir):
        """render() substitutes template variables."""
        template = assets_dir / "greeting.txt.j2"
        template.write_text("Hello, {{ name }}!")

        result = renderer.render("greeting.txt.j2", name="World")

        assert result == "Hello, World!"

    def test_render_raises_for_missing_template(self, renderer):
        """render() raises TemplateNotFoundError for missing templates."""
        with pytest.raises(TemplateNotFoundError):
            renderer.render("nonexistent.j2")

    def test_render_preserves_trailing_newline(self, renderer, assets_dir):
        """render() preserves trailing newlines in templates."""
        template = assets_dir / "with_newline.txt.j2"
        template.write_text("Content\n")

        result = renderer.render("with_newline.txt.j2")

        assert result == "Content\n"

    def test_render_nested_template(self, renderer, assets_dir):
        """render() works with templates in subdirectories."""
        subdir = assets_dir / "init"
        subdir.mkdir()
        template = subdir / "config.txt.j2"
        template.write_text("Project: {{ project }}")

        result = renderer.render("init/config.txt.j2", project="myproject")

        assert result == "Project: myproject"

    def test_write_creates_file(self, renderer, assets_dir, tmp_path):
        """write() creates the output file."""
        template = assets_dir / "test.txt.j2"
        template.write_text("Content")
        dest = tmp_path / "output.txt"

        renderer.write("test.txt.j2", dest)

        assert dest.exists()
        assert dest.read_text() == "Content"

    def test_write_creates_parent_directories(self, renderer, assets_dir, tmp_path):
        """write() creates parent directories if they don't exist."""
        template = assets_dir / "test.txt.j2"
        template.write_text("Content")
        dest = tmp_path / "nested" / "deep" / "output.txt"

        renderer.write("test.txt.j2", dest)

        assert dest.exists()
        assert dest.read_text() == "Content"

    def test_write_returns_path(self, renderer, assets_dir, tmp_path):
        """write() returns the destination path."""
        template = assets_dir / "test.txt.j2"
        template.write_text("Content")
        dest = tmp_path / "output.txt"

        result = renderer.write("test.txt.j2", dest)

        assert result == dest

    def test_write_substitutes_variables(self, renderer, assets_dir, tmp_path):
        """write() substitutes template variables."""
        template = assets_dir / "greeting.txt.j2"
        template.write_text("Hello, {{ name }}!")
        dest = tmp_path / "output.txt"

        renderer.write("greeting.txt.j2", dest, name="World")

        assert dest.read_text() == "Hello, World!"
