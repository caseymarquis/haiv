"""Test that dependencies are correctly wired."""


def test_can_import_mg():
    """Verify mg is available as a dependency."""
    from mg import Container

    assert Container is not None


def test_can_import_mg_core():
    """Verify mg-core itself imports."""
    import mg_core

    assert mg_core.__version__ == "0.1.0"
