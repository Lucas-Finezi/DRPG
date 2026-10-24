"""Engine prototype over the catalog: the goblin encounter must apply every call.

Four level-2 adventurers (Wizard, Cleric, Barbarian, Monk) fight six Goblin Warriors, reach
level 3 and fight six more. Every call the engine makes into the catalog must be OK or a GM
decision: no DATA_GAP (catalog lacks it) and no ENGINE_GAP (engine lacks it).

Usage: python3 -I -m unittest discover -s tests/engine -v
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.engine.calllog import CallLog  # noqa: E402
from tools.engine.simulate_goblins import run  # noqa: E402

SEEDS = range(2026, 2036)


class GoblinEncounter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = CallLog()
        cls.runs = [run(s, False, cls.log) for s in SEEDS]

    def test_no_gaps(self):
        bad = [f'{r["status"]} {r["kind"]} {r["name"]} {r["ref"]} {r["detail"]}' for r in self.log.problems()
               if r["status"] in ("DATA_GAP", "ENGINE_GAP")]
        self.assertEqual(bad, [])

    def test_only_gm_decision_is_the_level_up_premise(self):
        gm = {(r["kind"], r["name"]) for r in self.log.problems() if r["status"] == "GM"}
        self.assertEqual(gm, {("procedure", "level_3_by_xp")})

    def test_level_2_sheets(self):
        p = self.runs[0]["party_level_2"]
        self.assertEqual({n: (v["hp_max"], v["ac"]) for n, v in p.items()},
                         {"Wizard": (14, 14), "Cleric": (17, 14), "Barbarian": (23, 13), "Monk": (17, 15)})
        self.assertEqual(p["Wizard"]["slots"], {"1": 3})
        self.assertEqual(p["Barbarian"]["resources"]["rage"], 2)
        self.assertEqual(p["Monk"]["resources"]["focus_points"], 2)
        self.assertEqual(p["Monk"]["speed"], 40)          # Unarmored Movement +10
        self.assertEqual(p["Barbarian"]["speed"], 35)     # Goliath

    def test_level_3_sheets(self):
        p = self.runs[0]["party_level_3"]
        self.assertEqual({n: v["hp_max"] for n, v in p.items()}, {"Wizard": 20, "Cleric": 24, "Barbarian": 32, "Monk": 24})
        self.assertEqual({n: v["subclasses"] for n, v in p.items()},
                         {"Wizard": {"wizard": "evoker"}, "Cleric": {"cleric": "life-domain"},
                          "Barbarian": {"barbarian": "path-of-the-berserker"},
                          "Monk": {"monk": "warrior-of-the-open-hand"}})
        self.assertEqual(p["Wizard"]["slots"], {"1": 4, "2": 2})
        self.assertIn("flaming-sphere", p["Wizard"]["spellbook"])          # Evocation Savant, school per D-003
        self.assertIn("scorching-ray", p["Wizard"]["prepared"])
        self.assertIn("detect-magic", p["Wizard"]["always_prepared"])       # High Elf, character level 3
        self.assertTrue({"aid", "bless", "cure-wounds", "lesser-restoration"} <= set(p["Cleric"]["always_prepared"]))
        self.assertEqual(p["Barbarian"]["resources"]["rage"], 3)
        self.assertEqual(p["Monk"]["resources"]["focus_points"], 3)
        self.assertIn("monk-deflect-attacks", p["Monk"]["features"])
        self.assertIn("path-of-the-berserker-frenzy", p["Barbarian"]["features"])

    def test_xp(self):
        xp = self.runs[0]["xp"]
        self.assertEqual((xp["encounter_xp"], xp["each"], xp["needed_for_3"]), (300, 75, 900))


if __name__ == "__main__":
    unittest.main()
