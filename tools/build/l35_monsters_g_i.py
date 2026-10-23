#!/usr/bin/env python3
"""L35 — Creatures G–I (Monsters A–Z and Animals).

Usage: python3 -I tools/build/l35_monsters_g_i.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monsterlib import build_lot, write_lot  # noqa: E402

LOT = "L35"

if __name__ == "__main__":
    write_lot(LOT, build_lot(LOT))
