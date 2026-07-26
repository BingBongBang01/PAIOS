"""Repository scaffolding smoke test (WP-01).

Proves the build/test toolchain is wired end-to-end before any Phase 1
component exists. Later work packages add their own component-scoped
tests alongside their implementations, per
docs/930_Phase1_Development_Workflow.md.
"""

from paios import __version__
from paios.__main__ import main


def test_ci_smoke() -> None:
    assert True


def test_package_is_importable() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_entry_point_returns_success_exit_code() -> None:
    assert main() == 0
