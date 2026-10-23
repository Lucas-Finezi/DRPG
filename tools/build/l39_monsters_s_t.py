#!/usr/bin/env python3
"""L39 — Creatures S–T (Monsters A–Z and Animals).

Usage: python3 -I tools/build/l39_monsters_s_t.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from monsterlib import build_lot, write_lot  # noqa: E402

LOT = "L39"

if __name__ == "__main__":
    write_lot(LOT, build_lot(LOT))
