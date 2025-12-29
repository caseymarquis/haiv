"""Test that dependencies are correctly wired."""


def test_can_import_mg_core():
    """Verify mg-core is available as a dependency."""
    from mg_core import __version__

    assert __version__ == "0.1.0"


def test_can_import_mg_transitively():
    """Verify mg is available transitively via mg-core."""
    from mg import Container

    assert Container is not None


def test_can_import_mg_cli():
    """Verify mg_cli itself imports."""
    import mg_cli

    assert mg_cli.__version__ == "0.1.0"


def test_main_runs(monkeypatch):
    """Verify main entry point runs without error."""
    import sys
    from mg_cli import main

    # Mock sys.argv to avoid picking up pytest args
    monkeypatch.setattr(sys, "argv", ["mg"])

    # Should not raise - prints usage and returns
    main()
