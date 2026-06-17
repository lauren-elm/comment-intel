#!/usr/bin/env python
"""Launcher so the engine runs from anywhere without installation:

    python comment_intel.py <setup|doctor|rank|pull|gallery|run> [flags]

Adds its own folder to sys.path so the bundled `intel` package imports cleanly,
then hands off to the CLI. Pure standard library — no pip install required.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intel.__main__ import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
