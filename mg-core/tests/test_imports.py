"""Test that dependencies are correctly wired."""


def test_can_import_haiv():
    """Verify haiv is available as a dependency."""
    from haiv import Container

    assert Container is not None


def test_can_import_hv_core():
    """Verify haiv-core itself imports."""
    import haiv_core

    assert haiv_core.__version__ == "0.1.0"
