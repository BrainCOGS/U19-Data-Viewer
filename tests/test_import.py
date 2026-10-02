"""Import smoke tests.

Most viewer modules import `viewer.modules`, which calls
`dj.create_virtual_module` at import time and therefore needs a live DataJoint
database. Those imports are skipped cleanly when no database is reachable; the
DB-free modules are always checked.
"""

import importlib

import pytest

DB_FREE = ["viewer.utils", "viewer.busy_indicator", "viewer.updatable_figures"]
DB_BOUND = [
    "viewer.modules",
    "viewer.subject_filters",
    "viewer.subject_tab",
    "viewer.compare_tab",
    "viewer.session_tab",
    "viewer.plots.water_weight",
    "viewer.plots.psych_curve",
    "viewer.plots.performance_level",
]


@pytest.mark.parametrize("name", DB_FREE)
def test_import_without_database(name):
    assert importlib.import_module(name) is not None


@pytest.fixture(scope="module")
def database_available():
    try:
        importlib.import_module("viewer.modules")
    except Exception as exc:  # no config, no credentials, no server
        pytest.skip(f"no DataJoint database available: {type(exc).__name__}")


@pytest.mark.parametrize("name", DB_BOUND)
def test_import_with_database(database_available, name):
    assert importlib.import_module(name) is not None
