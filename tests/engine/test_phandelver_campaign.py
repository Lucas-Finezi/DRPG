"""The Phandelver campaign simulation (simulations/phandelver, simulation only).

Two groups of six cover the 12 classes. Each must finish the campaign at level 5 with no
ENGINE_GAP; the DATA_GAPs it meets are the known ones listed in docs/simulacao-phandelver.md.

Usage: python3 -I -m unittest discover -s tests/engine -v
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.engine.calllog import CallLog  # noqa: E402
from simulations.phandelver.run import GROUPS, play  # noqa: E402

KNOWN_DATA_GAPS = {"activation", "modifier", "proficiency", "reference", "grant", "item_state.wielded=this"}


class PhandelverCampaign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = CallLog()
        cls.runs = {g: play(g, 2026, cls.log) for g in GROUPS}

    def test_all_classes(self):
        classes = {c["class"] for r in self.runs.values() for c in r["created"]}
        self.assertEqual(len(classes), 12)

    def test_finished_at_level_5(self):
        for g, r in self.runs.items():
            self.assertFalse([s["name"] for s in r["scenes"] if s.get("skipped")], g)
            self.assertEqual({p["level"] for p in r["party"]}, {5}, g)

    def test_no_engine_gaps(self):
        bad = [f'{r["kind"]} {r["name"]} {r["ref"]}' for r in self.log.problems() if r["status"] == "ENGINE_GAP"]
        self.assertEqual(bad, [])

    def test_only_known_data_gaps(self):
        names = {r["name"] for r in self.log.problems() if r["status"] == "DATA_GAP"}
        self.assertLessEqual(names, KNOWN_DATA_GAPS)


if __name__ == "__main__":
    unittest.main()
