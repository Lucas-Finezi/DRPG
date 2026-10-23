#!/usr/bin/env python3
"""L38 — Creatures P–R (Monsters A–Z and Animals).

Usage: python3 -I tools/build/l38_monsters_p_r.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monsterlib import build_lot, write_lot  # noqa: E402

LOT = "L38"

if __name__ == "__main__":
    write_lot(LOT, build_lot(LOT))
