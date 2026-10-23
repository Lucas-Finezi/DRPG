#!/usr/bin/env python3
"""Rebuild every generated file from the extraction, in lot order, then run all checks.

  1. inventory (L00)
  2. clear knowledge/dnd5e/entries and run each lot builder (lNN_*.py) in lot order;
     L02 writes system.json first, later lots add the registry names they need
  3. L01 examples (they embed an excerpt of the final system.json)
  4. validate.py, selftest.py, coverage.py, refs.py

Usage: python3 -I tools/build/run_all.py [--extract]   (--extract also re-extracts the PDF)
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = [sys.executable, "-I"]


def run(*args):
    print("$", " ".join(str(a) for a in args[2:] if a != "-I"), flush=True)
    subprocess.run(list(args), check=True, cwd=ROOT)


def main():
    if "--extract" in sys.argv:
        run(*PY, "tools/extract/extract_srd.py", "source/SRD_CC_v5.2.1.pdf", "extraction")
    run(*PY, "tools/inventory/build_inventory.py")
    shutil.rmtree(ROOT / "knowledge" / "dnd5e" / "entries", ignore_errors=True)
    builders = sorted(p for p in (ROOT / "tools" / "build").glob("l[0-9][0-9]_*.py") if not p.name.startswith("l01_"))
    for b in sorted(builders, key=lambda p: int(re.match(r"l(\d+)_", p.name).group(1))):
        run(*PY, str(b.relative_to(ROOT)))
    run(*PY, "tools/build/l01_examples.py")
    run(*PY, "tools/validate/validate.py")
    run(*PY, "tools/validate/selftest.py")
    run(*PY, "tools/validate/coverage.py")
    run(*PY, "tools/validate/refs.py")


if __name__ == "__main__":
    main()
