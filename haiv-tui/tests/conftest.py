from harness import make_entry, make_sessions_deps, make_store

import pytest

from haiv_tui.store import TuiStore


@pytest.fixture
def store() -> TuiStore:
    return make_store()


@pytest.fixture
def sessions_deps(store: TuiStore) -> dict:
    return make_sessions_deps(store)
