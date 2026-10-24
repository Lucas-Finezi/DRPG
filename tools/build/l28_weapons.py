#!/usr/bin/env python3
"""L28 — Weapons: the Weapons section, Weapon Proficiency, the ten properties, the eight mastery
properties, the Improvised Weapons sidebar and the 38 weapons of the Weapons table.

Usage: python3 -I tools/build/l28_weapons.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, build, extend_registries, find, section, sidebar, slugify, write_entry  # noqa: E402
from itemlib import money, row_entry, table_rows, weight  # noqa: E402

LOT = "L28"
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
PROP = lambda s: f"dnd5e/weapon-property/{slugify(s)}"  # noqa: E731
MAST = lambda s: f"dnd5e/weapon-mastery/{slugify(s)}"  # noqa: E731
INHERIT = {"kind": "inherit"}
AMMO = {"Arrow": "dnd5e/gear/arrows", "Bolt": "dnd5e/gear/bolts", "Bullet": "dnd5e/gear/bullets-firearm",
        "Needle": "dnd5e/gear/needles"}


def parse_properties(text):
    out = []
    if text.strip() == "—":
        return out
    for part in re.split(r",\s*(?![^()]*\))", text):
        part = part.strip()
        m = re.fullmatch(r"(Ammunition|Thrown) \(Range (\d+)/(\d+)(?:; (\w+))?\)", part)
        if m:
            p = {"ref": PROP(m.group(1)), "range": {"normal_feet": int(m.group(2)), "long_feet": int(m.group(3))}}
            if m.group(4):
                p["ammunition"] = m.group(4).lower()
            out.append(p)
            continue
        m = re.fullmatch(r"Versatile \((\d+d\d+)\)", part)
        if m:
            out.append({"ref": PROP("Versatile"), "two_handed_damage": m.group(1)})
            continue
        m = re.fullmatch(r"Two-Handed \(unless mounted\)", part)
        if m:
            out.append({"ref": PROP("Two-Handed"), "unless": "mounted"})
            continue
        out.append({"ref": PROP(part)})
    return out


def ammo_ref(kind):
    return {"arrow": "dnd5e/gear/arrows", "bolt": "dnd5e/gear/bolts", "bullet": "dnd5e/gear/bullets-firearm",
            "needle": "dnd5e/gear/needles"}.get(kind)


def weapon_entries():
    E = []
    for group, n in table_rows("Weapons", 91):
        name, damage, props, mastery, wt, cost = n.cells
        cat = group.split()[0].lower()            # simple / martial
        kind = group.split()[1].lower()           # melee / ranged
        m = re.fullmatch(r"(\d+(?:d\d+)?) (\w+)", damage)
        dice, dtype = m.group(1), m.group(2).lower()
        properties = parse_properties(props)
        data = {"category": cat, "melee_or_ranged": kind, "damage": {"amount": int(dice) if dice.isdigit() else dice, "type": dtype},
                "properties": properties, "mastery": MAST(mastery), "weight_lb": weight(wt), "cost": money(cost)}
        attack = {"op": "attack", "attack_type": f"{kind}_weapon",
                  "on_hit": [{"op": "damage", "amount": int(dice) if dice.isdigit() else dice, "damage_type": dtype,
                              "note": "Plus the attack's ability modifier."}]}
        E.append(row_entry("weapon", name, n, LOT, f"Equipment/Weapons/Weapons/{group}/{name}", data,
                           items=[(None, "fx", attack), (None, "ref", [p["ref"] for p in properties] + [MAST(mastery)])],
                           facets={"category": cat, "melee_or_ranged": kind, "damage_type": dtype,
                                   "mastery": slugify(mastery), "cost_cp": data["cost"].get("cp", 0)}))
    return E


def H(title, kind, items, level=4, page=None, slug=None):
    pages = {"Ammunition": 89, "Finesse": 89, "Heavy": 89, "Light": 89}
    nodes = section(title, level, page=page or pages.get(title, 90))
    path = "Equipment/Weapons/" + ("Properties" if kind == "weapon-property" else "Mastery Properties") + f"/{title}"
    return build(kind, slug or slugify(title), title, nodes, LOT, path, items)


def property_entries():
    E = []
    E.append(H("Ammunition", "weapon-property", [
        (None, "rule", {"id": "ammunition", "requires_ammunition": True, "type_with_range": True, "expended_per_attack": 1,
                        "drawing_part_of_attack": True, "one_handed_loading_needs_free_hand": True}),
        ("After a fight, you can spend 1 minute", "rule", {"id": "recovery", "minutes": 1, "recover_fraction": 0.5,
                                                           "round": "down"})]))
    E.append(H("Finesse", "weapon-property", [(None, "fx", {
        "op": "choice", "id": "finesse_ability", "choose": 1, "options": [
            {"id": "str", "label": "Strength", "effects": [{"op": "modifier", "stat": "attack_ability", "mode": "set", "value": {"var": "ability_mod.str"}}]},
            {"id": "dex", "label": "Dexterity", "effects": [{"op": "modifier", "stat": "attack_ability", "mode": "set", "value": {"var": "ability_mod.dex"}}]}],
        "note": "Same modifier for the attack and damage rolls."})]))
    E.append(H("Heavy", "weapon-property", [(None, "fx", {
        "op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
        "when": {"any": [{"all": [{"pred": "attack_with_melee_weapon"}, {"pred": "ability_score_below", "args": {"ability": "str", "score": 13}}]},
                         {"all": [{"pred": "attack_with_ranged_weapon"}, {"pred": "ability_score_below", "args": {"ability": "dex", "score": 13}}]}]}})]))
    E.append(H("Light", "weapon-property", [(None, "fx", {
        "op": "trigger", "event": {"event": "takes_attack_action"}, "condition": {"pred": "attack_with_light_weapon"},
        "then": [{"op": "activation", "cost": "bonus_action", "then": [{"op": "attack", "attack_type": "melee_weapon",
                                                                        "ability_modifier_to_damage": "negative_only", "note": "With a different Light weapon; no ability modifier to damage unless negative."}]}]})]))
    E.append(H("Loading", "weapon-property", [(None, "rule", {"id": "loading", "max_ammunition_per_action_bonus_or_reaction": 1})]))
    E.append(H("Range", "weapon-property", [
        (None, "rule", {"id": "range", "normal_and_long_feet": True}),
        ("When attacking a target beyond normal range", "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
                                                               "when": {"pred": "beyond_normal_range"}}),
        ("When attacking a target beyond normal range", "fx", {"op": "restrict", "restrictions": ["attack_beyond_long_range"]})]))
    E.append(H("Reach", "weapon-property", [(None, "fx", {"op": "modifier", "stat": "reach", "mode": "add", "value": 5,
                                                          "note": "Also for Opportunity Attacks with it."})]))
    E.append(H("Thrown", "weapon-property", [(None, "rule", {"id": "thrown", "ranged_attack": True, "draw_as_part_of_attack": True,
                                                             "melee_weapon_uses_melee_ability": True})]))
    E.append(H("Two-Handed", "weapon-property", [(None, "rule", {"id": "two_handed", "hands_to_attack": 2})]))
    E.append(H("Versatile", "weapon-property", [(None, "rule", {"id": "versatile", "hands": [1, 2],
                                                                "two_handed_melee_damage": "value_in_parentheses"})]))
    return E


def mastery_entries():
    E = []
    hit = lambda then, cond=None, **kw: {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,  # noqa: E731
                                         **({"condition": cond} if cond else {}), "then": then, **kw}
    E.append(H("Cleave", "weapon-mastery", [(None, "fx", hit(
        [{"op": "attack", "attack_type": "melee_weapon", "ability_modifier_to_damage": "negative_only", "note": "A second creature within 5 feet of the first and within your reach; no ability modifier to damage unless negative."}],
        {"pred": "attack_with_melee_weapon"}, frequency={"count": 1, "per": "turn"}))]))
    E.append(H("Graze", "weapon-mastery", [(None, "fx", {
        "op": "trigger", "event": {"event": "misses_with_attack_roll"}, "optional": True,
        "then": [{"op": "damage", "amount": {"var": "attack_ability_mod"}, "damage_type": {"var": "chosen.weapon_damage_type"},
                  "target": INHERIT, "note": "Can be increased only by increasing the ability modifier."}]})]))
    E.append(H("Nick", "weapon-mastery", [(None, "rule", {"id": "nick", "light_extra_attack_part_of": "dnd5e/action/attack",
                                                          "once_per_turn": True, "property": PROP("Light")})]))
    E.append(H("Push", "weapon-mastery", [(None, "fx", hit([{"op": "move", "mode": "push", "distance_feet": 10,
                                                             "target": {"kind": "inherit", "filter": {"sizes": ["tiny", "small", "medium", "large"]}}}]))]))
    E.append(H("Sap", "weapon-mastery", [(None, "fx", hit([{"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
                                                            "target": INHERIT, "note": "Its next attack roll.",
                                                            "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "source"}}}]))]))
    E.append(H("Slow", "weapon-mastery", [(None, "fx", hit([{"op": "speed", "movement": "walk", "mode": "add", "value": -10, "target": INHERIT,
                                                             "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "source"}},
                                                             "note": "Only if damage was dealt; reductions from this property don't exceed 10 feet."}]))]))
    E.append(H("Topple", "weapon-mastery", [(None, "fx", hit([{"op": "save", "ability": "con", "target": INHERIT,
                                                               "dc": {"op": "add", "args": [8, {"var": "attack_ability_mod"}, {"var": "proficiency_bonus"}]},
                                                               "on_fail": [{"op": "apply_condition", "condition": C("prone")}]}]))]))
    E.append(H("Vex", "weapon-mastery", [(None, "fx", hit([{"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                                                            "direction": "against", "target": INHERIT,
                                                            "when": {"pred": "roller_is_source"},
                                                            "note": "Your next attack roll against that creature; only if damage was dealt.",
                                                            "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "source", "which": "next"},
                                                                         "ends_on": [{"event": "targeted_by_attack_roll", "whose": "target"}]}}]))]))
    return E


def section_entries():
    E = []
    wi = find("Weapons", 5, 91)
    table_head = [NODES[wi]] + [n for n in NODES[wi + 1:wi + 60] if (n.type == "t" and n.text.startswith("| **"))
                                or (n.type == "p" and n.text.startswith("*") and n.text.endswith("Weapons*"))]
    nodes = section("Weapons", 2, stop_titles=("Weapon Proficiency",)) + table_head
    E.append(build("rule", "weapons", "Weapons", nodes, LOT, "Equipment/Weapons", [
        (None, "rule", {"id": "table_columns", "columns": ["name", "damage", "properties", "mastery", "weight", "cost"]}),
        ("**Category.**", "rule", {"id": "category", "values": ["simple", "martial"]}),
        ("**Melee or Ranged.**", "rule", {"id": "melee_or_ranged", "melee_reach_feet": 5, "ranged": "greater_distance"}),
        ("**Damage.**", "rule", {"id": "damage", "listed_with_type": True}),
        ("**Properties.**", "ref", ["dnd5e/rule/properties"]),
        ("**Mastery.**", "ref", ["dnd5e/rule/mastery-properties"]),
        ("**Mastery.**", "rule", {"id": "mastery", "requires_feature": True}),
        ("##### Weapons", "rule", {"id": "weapons_table", "groups": ["simple_melee", "simple_ranged", "martial_melee", "martial_ranged"],
                                   "rows": "dnd5e/weapon/*"})]))
    E.append(build("rule", "weapon-proficiency", "Weapon Proficiency", section("Weapon Proficiency", 3), LOT,
                   "Equipment/Weapons/Weapon Proficiency", [
                       (None, "rule", {"id": "proficiency", "anyone_can_wield": True, "proficiency_adds_bonus_to_attack": True,
                                       "monsters_proficient_with_stat_block_weapons": True})]))
    E.append(build("rule", "properties", "Properties", section("Properties", 3, page=89, stop_titles=("Ammunition",)), LOT,
                   "Equipment/Weapons/Properties", [(None, "rule", {"id": "properties", "entries": "dnd5e/weapon-property/*"})]))
    E.append(build("rule", "mastery-properties", "Mastery Properties", section("Mastery Properties", 3, stop_titles=("Cleave",)), LOT,
                   "Equipment/Weapons/Mastery Properties", [(None, "rule", {"id": "mastery", "requires_feature": "e.g. Weapon Mastery",
                                                                            "entries": "dnd5e/weapon-mastery/*"})]))
    E.append(build("rule", "sidebar-improvised-weapons", "Improvised Weapons", sidebar("Improvised Weapons"), LOT,
                   "Equipment/Weapons/Properties", [(None, "ref", ["dnd5e/rule/improvised-weapons"])]))
    return E


REGISTRY = {
    "variables": [{"id": "attack_ability_mod", "description": "The ability modifier used for the attack roll.", "type": "number", "pages": [90]}],
    "restrictions": [{"id": "attack_beyond_long_range", "description": "The creature can't attack a target beyond the weapon's long range.", "pages": [90]}],
    "predicates": [
        {"id": "ability_score_below", "description": "The creature's ability score (param) is below a value (param).", "params": ["ability", "score"], "type": "predicate", "pages": [89]},
        {"id": "attack_with_light_weapon", "description": "The attack uses a Light weapon.", "type": "predicate", "pages": [89]},
        {"id": "roller_is_source", "description": "The creature making the roll is the source of this effect (e.g. the attacker who applied Vex).", "type": "predicate", "pages": [90]}],
    "events": [{"id": "targeted_by_attack_roll", "description": "An attack roll is made against the creature (an effect ending on it is used up by that roll).", "type": "event", "pages": [90, 110]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = section_entries() + property_entries() + mastery_entries() + weapon_entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
