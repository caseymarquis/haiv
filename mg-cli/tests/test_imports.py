"""Test that dependencies are correctly wired."""


def test_can_import_hv_core():
    """Verify haiv-core is available as a dependency."""
    from haiv_core import __version__

    assert __version__ == "0.1.0"


def test_can_import_hv_transitively():
    """Verify haiv is available transitively via haiv-core."""
    from haiv import Container

    assert Container is not None


def test_can_import_hv_cli():
    """Verify haiv_cli itself imports."""
    import haiv_cli

    assert haiv_cli.__version__ == "0.1.0"


def test_main_runs(monkeypatch):
    """Verify main entry point runs without error."""
    import sys
    from haiv_cli import main

    # Mock sys.argv to avoid picking up pytest args
    monkeypatch.setattr(sys, "argv", ["hv"])

    # Should not raise - prints usage and returns
    main()
