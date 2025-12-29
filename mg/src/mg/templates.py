"""Template rendering utilities for mg commands."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


class TemplateNotFoundError(Exception):
    """Raised when a template cannot be found."""

    pass


class TemplateRenderer:
    """Renders Jinja2 templates from a package's __assets__ directory.

    Usage:
        renderer = TemplateRenderer(assets_path)
        content = renderer.render("init/CLAUDE.md.j2", project="myproject")
        renderer.write("init/CLAUDE.md.j2", dest_path, project="myproject")
    """

    def __init__(self, assets_path: Path) -> None:
        """Initialize with the path to the assets directory.

        Args:
            assets_path: Path to the __assets__ directory containing templates.
        """
        self._env = Environment(
            loader=FileSystemLoader(assets_path),
            keep_trailing_newline=True,
        )

    def render(self, template_path: str, **variables) -> str:
        """Render a template to a string.

        Args:
            template_path: Path to the template relative to assets directory.
            **variables: Variables to substitute in the template.

        Returns:
            The rendered template as a string.

        Raises:
            TemplateNotFoundError: If the template doesn't exist.
        """
        try:
            template = self._env.get_template(template_path)
        except TemplateNotFound as e:
            raise TemplateNotFoundError(f"Template not found: {template_path}") from e

        return template.render(**variables)

    def write(self, template_path: str, dest: Path, **variables) -> Path:
        """Render a template and write it to a file.

        Args:
            template_path: Path to the template relative to assets directory.
            dest: Destination path for the rendered file.
            **variables: Variables to substitute in the template.

        Returns:
            The destination path.

        Raises:
            TemplateNotFoundError: If the template doesn't exist.
        """
        content = self.render(template_path, **variables)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)
        return dest
