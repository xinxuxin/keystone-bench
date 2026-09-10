#!/usr/bin/env python3
"""Rebuild the release from HealthBench and the shipped edits.

Kept as an entry point for CI, the Makefile and anyone working in a checkout; the implementation lives in
`keystone/build.py` so that an installation from PyPI can do the same thing with `keystone build`.
"""
import sys
from pathlib import Path

try:
    from keystone.build import main
except ModuleNotFoundError:            # a checkout that has not been pip-installed
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from keystone.build import main

if __name__ == "__main__":
    raise SystemExit(main())
