"""Root conftest that prevents running tests from workspace root."""

import pytest
from pathlib import Path


def pytest_configure(config):
    """Prevent running tests from workspace root."""
    rootdir = Path(config.rootdir)
    pyproject = rootdir / "pyproject.toml"

    if pyproject.exists() and "[tool.uv.workspace]" in pyproject.read_text():
        raise pytest.UsageError(
            "Cannot run tests from workspace root.\n\n"
            "Run tests for all packages:\n"
            "  ./test-all.sh\n\n"
            "Or run individually:\n"
            "  cd mg && uv run pytest\n"
            "  cd mg-core && uv run pytest\n"
            "  cd mg-cli && uv run pytest"
        )
