#!/usr/bin/env python3
"""Compatibility launcher for C2A runtime."""

from pathlib import Path
import sys

RUNTIME_DIR = Path(__file__).parent / "c2a_runtime"
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from C2A import main  # type: ignore  # pylint: disable=import-error


if __name__ == "__main__":
    main()
