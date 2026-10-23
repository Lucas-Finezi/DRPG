#!/usr/bin/env python3
"""L29 — Armor and shields: the Armor section, Armor Training, One at a Time and the 13 entries
of the Armor table.

Usage: python3 -I tools/build/l29_armor.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, find, section, slugify, write_entry  # noqa: E402
from itemlib import money, row_entry, table_rows, weight  # noqa: E402

LOT = "L29"
DEX = {"var": "ability_mod.dex"}
DON = {  # group label -> (category, don minutes or 'utilize', doff minutes or 'utilize')
    "Light Armor (1 Minute to Don or Doff)": ("light", 1, 1),
    "Medium Armor (5 Minutes to Don and 1 Minute to Doff)": ("medium", 5, 1),
    "Heavy Armor (10 Minutes to Don and 5 Minutes to Doff)": ("heavy", 10, 5),
    "Shield (Utilize Action to Don or Doff)": ("shield", "dnd5e/action/utilize", "dnd5e/action/utilize"),
}


def armor_entries():
    E = []
    for group, n in table_rows("Armor", 92):
        name, ac, strength, stealth, wt, cost = n.cells
        cat, don, doff = DON[group]
        worn = {"pred": "wearing_item", "args": {"item": slugify(name)}}
        data = {"category": cat, "don": don, "doff": doff, "weight_lb": weight(wt), "cost": money(cost)}
        fx = []
        m = re.fullmatch(r"(\d+)( \+ Dex modifier)?(?: \(max (\d)\))?", ac)
        if m:
            base = int(m.group(1))
            value = base if not m.group(2) else {"op": "add", "args": [base, DEX if not m.group(3) else
                                                                        {"op": "min", "args": [DEX, int(m.group(3))]}]}
            data["armor_class"] = {"base": base, "dex_modifier": bool(m.group(2)),
                                   **({"dex_max": int(m.group(3))} if m.group(3) else {})}
            fx.append({"op": "modifier", "stat": "base_ac", "mode": "set", "value": value, "when": worn})
        else:  # Shield: +2
            data["armor_class"] = {"bonus": int(ac.replace("+", ""))}
            fx.append({"op": "modifier", "stat": "ac", "mode": "add", "value": int(ac.replace("+", "")),
                       "when": {"pred": "wielding_item", "args": {"item": slugify(name)}}})
        if strength != "—":
            score = int(strength.split()[1])
            data["strength_requirement"] = score
            fx.append({"op": "speed", "movement": "walk", "mode": "add", "value": -10,
                       "when": {"all": [worn, {"pred": "ability_score_below", "args": {"ability": "str", "score": score}}]}})
        if stealth == "Disadvantage":
            data["stealth_disadvantage"] = True
            fx.append({"op": "roll_mode", "mode": "disadvantage", "rolls": ["ability_check.dex"],
                       "when": {"all": [worn, {"pred": "check_uses_skill", "args": {"skill": "stealth"}}]}})
        E.append(row_entry("armor", name, n, LOT, f"Equipment/Armor/Armor/{group}/{name}", data,
                           items=[(None, "fx", fx), (None, "ref", ["dnd5e/rule/armor-training", "dnd5e/rule/equipment-armor-training"])],
                           facets={"category": cat, "cost_cp": data["cost"].get("cp", 0),
                                   "stealth_disadvantage": bool(data.get("stealth_disadvantage"))}))
    return E


def section_entries():
    E = []
    ai = find("Armor", 5, 92)
    table_head = [NODES[ai]] + [n for n in NODES[ai + 1:ai + 30] if (n.type == "t" and n.text.startswith("| **"))
                                or (n.type == "p" and n.text.strip("*") in DON)]
    E.append(build("rule", "armor", "Armor", section("Armor", 2, page=92, stop_titles=("Armor Training",)) + table_head, LOT,
                   "Equipment/Armor", [
                       (None, "rule", {"id": "table_columns", "columns": ["armor", "armor_class", "strength", "stealth", "weight", "cost"]}),
                       ("**Category.**", "rule", {"id": "category", "values": ["light", "medium", "heavy"], "determines": "don_and_doff_time"}),
                       ("**Armor Class (AC).**", "rule", {"id": "armor_class", "column_gives": "base_ac"}),
                       ("**Strength.**", "rule", {"id": "strength", "speed_reduction_feet": 10, "unless_strength_at_least": "listed_score"}),
                       ("**Stealth.**", "rule", {"id": "stealth", "disadvantage_on": "dexterity_stealth_checks"}),
                       ("##### Armor", "rule", {"id": "armor_table", "groups": list(DON), "rows": "dnd5e/armor/*"})]))
    E.append(build("rule", "equipment-armor-training", "Armor Training", section("Armor Training", 3, page=92), LOT,
                   "Equipment/Armor/Armor Training", [
                       (None, "rule", {"id": "training", "anyone_can_don": True, "training_from_class_or_features": True,
                                       "monsters_trained_with_stat_block_armor": True}),
                       ("#### Light, Medium, or Heavy Armor", "fx", [
                           {"op": "roll_mode", "mode": "disadvantage", "rolls": ["d20_test.str", "d20_test.dex"],
                            "when": {"pred": "wearing_untrained_armor"}},
                           {"op": "restrict", "restrictions": ["cast_spells"], "when": {"pred": "wearing_untrained_armor"}}]),
                       ("#### Shield", "fx", {"op": "restrict", "restrictions": ["shield_ac_bonus"],
                                             "when": {"pred": "using_untrained_shield"}})]))
    E.append(build("rule", "one-at-a-time", "One at a Time", section("One at a Time", 3), LOT, "Equipment/Armor/One at a Time", [
        (None, "rule", {"id": "one_at_a_time", "max_armor_suits": 1, "max_shields": 1})]))
    return E


REGISTRY = {
    "predicates": [
        {"id": "wearing_item", "description": "The creature wears this item (param: item slug).", "params": ["item"], "type": "predicate", "pages": [92]},
        {"id": "wielding_item", "description": "The creature wields this item (param: item slug).", "params": ["item"], "type": "predicate", "pages": [92]}],
}

if __name__ == "__main__":
    from entrylib import extend_registries
    extend_registries(REGISTRY, LOT)
    out = section_entries() + armor_entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
