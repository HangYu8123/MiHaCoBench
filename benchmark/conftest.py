"""Root conftest for HarnessFlow PyBench.

Ensures the ``benchmark/`` directory is importable so every grader can do
``from _lib import grading_utils as gu`` regardless of where pytest is invoked
from, and registers the soft markers used by graders.
"""
import sys
from pathlib import Path

BENCH_ROOT = Path(__file__).resolve().parent
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "soft_complexity: empirical Big-O scaling fit — advisory, not a hard gate",
    )
    config.addinivalue_line(
        "markers",
        "code_quality: advisory AST-based code-quality report — never pass/fail",
    )
