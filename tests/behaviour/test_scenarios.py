"""L45 — Behaviour tests over the generated catalog.

Each scenario reads entries as an engine would and checks the outcome against the source
text: combat (attacks, saves, damage), magic (upcasting, healing), rests, levels, resources,
conditions, items, creatures and traps. A small deterministic evaluator computes expressions
with dice at their average, minimum or maximum.

Usage: python3 -I -m unittest discover -s tests/behaviour -v
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENT = ROOT / "knowledge" / "dnd5e" / "entries"
SYSTEM = json.loads((ROOT / "knowledge" / "dnd5e" / "system.json").read_text(encoding="utf-8"))


def E(ref):
    kind, slug = ref.split("/")[-2:]
    return json.loads((ENT / kind / f"{slug}.json").read_text(encoding="utf-8"))


def ev(x, env=None, mode="max"):
    """Evaluate an expression; dice at 'max', 'min' or 'avg'."""
    env = env or {}
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        m = re.fullmatch(r"(\d+)d(\d+)", x)
        if not m:
            raise ValueError(x)
        n, f = int(m.group(1)), int(m.group(2))
        return {"max": n * f, "min": n, "avg": n * (f + 1) / 2}[mode]
    if "var" in x:
        return env[x["var"]]
    if "dice" in x:
        n, f = ev(x["dice"]["count"], env, mode), x["dice"]["faces"]
        return {"max": n * f, "min": n, "avg": n * (f + 1) / 2}[mode]
    if "op" in x:
        a = [ev(y, env, mode) for y in x["args"]]
        op = x["op"]
        if op == "add":
            return sum(a)
        if op == "sub":
            return a[0] - sum(a[1:])
        if op == "mul":
            r = 1
            for v in a:
                r *= v
            return r
        if op == "div":
            return a[0] // a[1] if x.get("round", "down") == "down" else a[0] / a[1]
        if op == "min":
            return min(a)
        if op == "max":
            return max(a)
        if op == "neg":
            return -a[0]
    if "table" in x:
        cls = E(x["table"])
        row = cls["data"]["levels"][str(ev(x["key"], env, mode))]["columns"][x["column"]]
        return int(row.replace("+", ""))
    if "scale" in x:
        v = env[x["scale"]["by"]]
        out = None
        for st in x["scale"]["steps"]:
            if v >= st["from"]:
                out = st["value"]
        return out
    raise ValueError(x)


def find(effects, op, **match):
    """Depth-first search for an effect with this op (and matching keys)."""
    for e in effects if isinstance(effects, list) else [effects]:
        if not isinstance(e, dict):
            continue
        if e.get("op") == op and all(e.get(k) == v for k, v in match.items()):
            return e
        for k in ("then", "on_hit", "on_fail", "on_success", "effects"):
            if k in e:
                r = find(e[k], op, **match)
                if r:
                    return r
        for o in e.get("options", []):
            r = find(o.get("effects", []), op, **match)
            if r:
                return r
    return None


class Combat(unittest.TestCase):
    def test_goblin_scimitar(self):
        g = E("dnd5e/creature/goblin-warrior")
        atk = find(g["effects"], "attack")
        self.assertEqual(atk["bonus"], 4)
        dmg = atk["on_hit"][0]
        self.assertEqual(dmg["damage_type"], "slashing")
        self.assertEqual(ev(dmg["amount"], mode="avg"), 5.5)  # printed 5 (1d6 + 2), average rounded down
        self.assertEqual(len(atk["on_hit"]), 1, "the extra 1d4 needs Advantage: left to the rider decision")

    def test_longsword_versatile(self):
        w = E("dnd5e/weapon/longsword")["data"]
        self.assertEqual((w["damage"]["amount"], w["damage"]["type"]), ("1d8", "slashing"))
        self.assertEqual(w["properties"][0]["two_handed_damage"], "1d10")

    def test_plate_armor(self):
        a = E("dnd5e/armor/plate-armor")["data"]
        self.assertEqual(a["armor_class"]["base"], 18)
        self.assertFalse(a["armor_class"]["dex_modifier"])
        self.assertEqual(a["strength_requirement"], 15)

    def test_aboleth_legendary_resistance(self):
        a = E("dnd5e/creature/aboleth")
        lr = next(e for e in a["effects"] if e.get("op") == "trigger" and e["event"]["event"] == "fails_saving_throw")
        self.assertEqual(lr["frequency"], {"count": 3, "per": "day"})
        self.assertEqual(a["data"]["cr"]["xp"], 5900)
        self.assertEqual(a["data"]["cr"]["xp_in_lair"], 7200)


class Magic(unittest.TestCase):
    def test_fireball_upcast(self):
        f = E("dnd5e/spell/fireball")
        sv = find(f["effects"], "save", ability="dex")
        self.assertTrue(sv["half_on_success"])
        self.assertEqual(sv["target"]["area"], {"shape": "sphere", "size_feet": 20, "origin": "point"})
        d = sv["on_fail"][0]
        self.assertEqual(ev(d["amount"], {"spell_slot_level": 3}), 48)   # 8d6
        self.assertEqual(ev(d["amount"], {"spell_slot_level": 5}), 60)   # 10d6
        self.assertEqual(f["facets"]["classes"], ["sorcerer", "wizard"])

    def test_cure_wounds(self):
        h = find(E("dnd5e/spell/cure-wounds")["effects"], "heal")
        self.assertEqual(ev(h["amount"], {"spell_slot_level": 1, "spellcasting_mod": 3}), 19)  # 2d8 + 3
        self.assertEqual(ev(h["amount"], {"spell_slot_level": 2, "spellcasting_mod": 3}), 35)  # 4d8 + 3

    def test_wand_of_fireballs_upcast_by_charges(self):
        w = E("dnd5e/magic-item/wand-of-fireballs")
        c = find(w["effects"], "cast_spell")
        self.assertEqual(c["spell"], "dnd5e/spell/fireball")
        self.assertEqual(ev(c["level"], {"charges_spent": 3}), 5)
        res = find(w["effects"], "resource")
        self.assertEqual(res["max"], 7)


class Rests(unittest.TestCase):
    def test_long_rest(self):
        lr = E("dnd5e/rule/long-rest")["effects"]
        self.assertEqual(find(lr, "heal")["amount"], {"var": "hp_max"})
        self.assertEqual(find(lr, "restore", resource="hit_point_dice")["amount"], "all")
        self.assertEqual(find(lr, "remove_condition")["levels"], 1)

    def test_short_rest_hit_die(self):
        h = find(E("dnd5e/rule/short-rest")["effects"], "heal")
        self.assertEqual(ev(h["amount"], {"hit_point_die": 1, "ability_mod.con": -3}), 1)  # minimum 1


class Levels(unittest.TestCase):
    def test_proficiency_bonus(self):
        pb = SYSTEM["proficiency_bonus"]["by_level"]
        self.assertEqual((pb["1"], pb["5"], pb["9"], pb["13"], pb["17"]), (2, 3, 4, 5, 6))

    def test_xp_thresholds(self):
        adv = {a["level"]: a["xp"] for a in SYSTEM["levels"]["advancement"]}
        self.assertEqual((adv[2], adv[5], adv[20]), (300, 6500, 355000))


class Resources(unittest.TestCase):
    def test_barbarian_rages(self):
        r = find(E("dnd5e/feature/barbarian-rage")["effects"], "resource", resource="rage")
        self.assertEqual(ev(r["max"], {"class_level.barbarian": 1}), 2)
        self.assertEqual(ev(r["max"], {"class_level.barbarian": 17}), 6)

    def test_staff_of_power_charges(self):
        s = E("dnd5e/magic-item/staff-of-power")
        self.assertEqual(find(s["effects"], "resource")["max"], 20)


class Conditions(unittest.TestCase):
    def test_exhaustion(self):
        fx = E("dnd5e/condition/exhaustion")["effects"]
        self.assertEqual(ev(fx[0]["value"], {"condition_level.exhaustion": 3}), -6)
        self.assertEqual(ev(fx[1]["value"], {"condition_level.exhaustion": 3}), -15)

    def test_prone_stand_up(self):
        fx = E("dnd5e/condition/prone")["effects"]
        self.assertIn("move_except_crawl", fx[0]["restrictions"])
        stand = find(fx, "activation")
        self.assertEqual(ev(stand["movement_cost"], {"speed.walk": 30}), 15)


class Items(unittest.TestCase):
    def test_cloak_of_protection(self):
        fx = E("dnd5e/magic-item/cloak-of-protection")["effects"]
        self.assertEqual([(e["stat"], e["value"]) for e in fx], [("ac", 1), ("saving_throw", 1)])
        self.assertEqual(fx[0]["when"], {"pred": "item_state", "args": {"item": "this", "state": "worn"}})

    def test_potions_of_healing(self):
        v = E("dnd5e/magic-item/potions-of-healing")["data"]["item"]["variants"]
        self.assertEqual([x["hp_regained"] for x in v], ["2d4 + 2", "4d4 + 4", "8d4 + 8", "10d4 + 20"])

    def test_serpent_venom(self):
        sv = E("dnd5e/poison/serpent-venom")["effects"][0]
        self.assertEqual((sv["ability"], sv["dc"], sv["half_on_success"]), ("con", 11, True))
        self.assertEqual(ev(sv["on_fail"][0]["amount"], mode="avg"), 10.5)


class Traps(unittest.TestCase):
    def test_collapsing_roof(self):
        t = E("dnd5e/trap/collapsing-roof")
        sv = find(t["effects"], "save")
        self.assertEqual((sv["ability"], sv["dc"]), ("dex", 13))
        self.assertEqual(ev(sv["on_fail"][0]["amount"], mode="max"), 20)
        self.assertEqual(t["facets"]["severity"], ["deadly"])


class Integrity(unittest.TestCase):
    def test_coverage_reproduces_text(self):
        """Every entry's coverage segments, joined, reproduce its text (whitespace aside)."""
        norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
        for p in ENT.rglob("*.json"):
            e = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(norm("".join(s["text"] for s in e["coverage"])), norm(e["text"]), e["ref"])

    def test_every_master_decision_is_cited(self):
        for p in ENT.rglob("*.json"):
            e = json.loads(p.read_text(encoding="utf-8"))
            ids = {m["id"] for m in e.get("master_decisions", [])}
            cited = {b[3:] for s in e["coverage"] for b in s.get("by", []) if b.startswith("md:")}
            self.assertEqual(ids, cited, e["ref"])


if __name__ == "__main__":
    unittest.main()
