#!/usr/bin/env python3
"""L45 — Behaviour tests: runs tests/behaviour (combat, magic, rests, levels, resources,
conditions, items, traps, catalog integrity) and fails the build if any scenario fails.

Usage: python3 -I tools/build/l45_behaviour_tests.py
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    r = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests/behaviour"], cwd=ROOT)
    sys.exit(r.returncode)
