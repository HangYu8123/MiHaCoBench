"""HarnessFlow PyBench — shared grading library.

This package is intentionally importable both as ``benchmark._lib`` and, when the
``benchmark/`` directory is on ``sys.path`` (the default for the grader runner),
as ``_lib``. Graders import helpers via ``from _lib import grading_utils as gu``.
"""
