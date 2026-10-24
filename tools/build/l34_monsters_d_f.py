#!/usr/bin/env python3
"""L34 — Creatures D–F (Monsters A–Z and Animals).

Usage: python3 -I tools/build/l34_monsters_d_f.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monsterlib import build_lot, write_lot  # noqa: E402

LOT = "L34"

if __name__ == "__main__":
    write_lot(LOT, build_lot(LOT))
