#!/usr/bin/env python3
"""L01 — valid examples for every base schema (schema/examples/*.example.json).

Examples use real SRD 5.2.1 text taken verbatim through entrylib, so they double as tests of
the contract against actual content. The catalog-entry examples anticipate the format the
spell and condition lots (L03, L17-L26) will produce; those lots own the real entries.

Usage: python3 -I tools/build/l01_examples.py
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import entry, md, render, section, source  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "schema" / "examples"
LOT = "L01"
SYS = "dnd5e/system/dnd5e"


def dump(name, obj):
    OUT.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, dict) and "ref" in obj and "$schema" in obj:
        obj["$schema"] = "../catalog_entry.schema.json"
    (OUT / f"{name}.example.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def upcast(base_count, base_level, faces):
    """count = base + (slot level - base level)."""
    return {"dice": {"count": {"op": "add", "args": [base_count, {"op": "sub", "args": [
        {"var": "spell_slot_level"}, base_level]}]}, "faces": faces}}


def spell_header_plan():
    return [(None, "structured", ["/facets", "/data"])]


def main():
    # ---------------------------------------------------------------- fragments
    dump("source", source([132], "Spells/Spell Descriptions/Fireball", "L20"))
    dump("expression.dice", "8d6")
    dump("expression.upcast", upcast(8, 3, 6))
    dump("expression.scale", {"scale": {"by": "level", "steps": [
        {"from": 1, "value": "1d10"}, {"from": 5, "value": "2d10"}, {"from": 11, "value": "3d10"},
        {"from": 17, "value": "4d10"}]}})
    dump("expression.lookup", {"table": "dnd5e/class/barbarian", "table_id": "barbarian_features",
                               "key": {"var": "class_level.barbarian"}, "column": "Rages"})
    dump("duration.concentration", {"kind": "minutes", "amount": 1, "up_to": True, "concentration": True,
                                    "text": "Concentration, up to 1 minute"})
    dump("duration.until_event", {"kind": "until_event", "until": {"event": "turn_start", "whose": "self",
                                                                   "which": "next"},
                                  "text": "Until the start of your next turn"})
    fireball_target = {"kind": "area", "range": {"kind": "distance", "feet": 150},
                       "area": {"shape": "sphere", "size_feet": 20, "origin": "point"}}
    dump("target.sphere", fireball_target)
    hold_target = {"kind": "creature", "count": {"op": "add", "args": [1, {"op": "sub", "args": [
        {"var": "spell_slot_level"}, 2]}]}, "range": {"kind": "distance", "feet": 60}, "must_see": True,
        "distinct": True, "filter": {"creature_types": ["humanoid"]}}
    dump("target.creatures", hold_target)
    fireball_effect = {"op": "save", "ability": "dex", "dc": {"var": "spell_save_dc"}, "target": fireball_target,
                       "on_fail": [{"op": "damage", "amount": upcast(8, 3, 6), "damage_type": "fire"}],
                       "half_on_success": True}
    dump("effect.save_damage", fireball_effect)
    shield_effect = {"op": "trigger", "event": {"event": "hit_by_attack_roll", "whose": "self"}, "cost": "reaction",
                     "optional": True, "then": [{"op": "cast_spell", "spell": "dnd5e/spell/shield"}]}
    dump("effect.trigger", shield_effect)
    dump("master_decision", md("flammable_objects", "Which flammable objects in the area, not worn or carried, "
                               "start burning?", "Flammable objects in the area that aren’t being worn or carried "
                               "start burning.", reason="not_automatable", pages=[132]))

    # ---------------------------------------------------------------- catalog entries
    # condition
    nodes = section("Poisoned [Condition]", 4)
    e = entry("condition", "poisoned", "Poisoned", nodes, LOT, "Rules Glossary/Rules Definitions/Poisoned [Condition]", [
        (None, "structured", ["/effects"]),
        ("***Ability Checks and Attacks Affected.***", "structured", ["/effects/0"])],
        effects=[{"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll", "ability_check"],
                  "direction": "own", "when": {"pred": "has_condition", "args": {"condition": "poisoned"}}}])
    dump("catalog_entry.condition-poisoned", e)

    # spell: save + area + damage + upcast + master decision
    nodes = section("Fireball", 4)
    # section() stops at the embedded stat block printed after Fireball (a level-3 heading)
    fx = copy.deepcopy(fireball_effect)
    fx["id"] = "explosion"
    e = entry("spell", "fireball", "Fireball", nodes, LOT, "Spells/Spell Descriptions/Fireball", [
        (None, "structured", ["/facets", "/data"]),
        ("A bright streak flashes", "structured", ["/effects/0"]),
        ("Flammable objects in the area", "master_decision", ["md:flammable_objects", "dnd5e/hazard/burning"]),
        ("***Using a Higher-Level Spell Slot.***", "structured", ["/effects/0/on_fail/0/amount"])],
        facets={"level": 3, "school": "evocation", "classes": ["sorcerer", "wizard"], "concentration": False,
                "ritual": False},
        data={"casting_time": {"cost": "action"}, "range": {"kind": "distance", "feet": 150},
              "components": {"verbal": True, "somatic": True, "material": "a ball of bat guano and sulfur"},
              "duration": {"kind": "instantaneous"}},
        effects=[fx, {"op": "master_decision", "decision": "flammable_objects"}],
        master_decisions=[md("flammable_objects", "Which flammable objects in the area, not worn or carried, "
                             "start burning?", "Flammable objects in the area that aren’t being worn or carried "
                             "start burning.", reason="not_automatable", pages=[132])])
    dump("catalog_entry.spell-fireball", e)

    # spell: targets that scale, save each turn, concentration, condition
    nodes = section("Hold Person", 4)
    e = entry("spell", "hold-person", "Hold Person", nodes, LOT, "Spells/Spell Descriptions/Hold Person", [
        (None, "structured", ["/facets", "/data"]),
        ("Choose a Humanoid", "structured", ["/effects/0"]),
        ("At the end of each of its turns", "structured", ["/effects/0/repeat"]),
        ("***Using a Higher-Level Spell Slot.***", "structured", ["/effects/0/target/count"])],
        facets={"level": 2, "school": "enchantment", "classes": ["bard", "cleric", "druid", "sorcerer", "warlock",
                                                                 "wizard"], "concentration": True, "ritual": False},
        data={"casting_time": {"cost": "action"}, "range": {"kind": "distance", "feet": 60},
              "components": {"verbal": True, "somatic": True, "material": "a straight piece of iron"},
              "duration": {"kind": "minutes", "amount": 1, "up_to": True, "concentration": True,
                           "text": "Concentration, up to 1 minute"}},
        effects=[{"op": "save", "ability": "wis", "dc": {"var": "spell_save_dc"}, "target": hold_target,
                  "on_fail": [{"op": "apply_condition", "condition": "dnd5e/condition/paralyzed",
                               "duration": {"kind": "minutes", "amount": 1, "up_to": True, "concentration": True}}],
                  "repeat": {"on": {"event": "turn_end", "whose": "target", "which": "each"},
                             "ends": "effect_on_self"}}])
    dump("catalog_entry.spell-hold-person", e)

    # spell: reaction trigger, AC bonus until an event, immunity to one spell's damage
    nodes = section("Shield", 4, page=161)
    e = entry("spell", "shield", "Shield", nodes, LOT, "Spells/Spell Descriptions/Shield", [
        (None, "structured", ["/facets", "/data"]),
        ("An imperceptible barrier", "structured", ["/effects/0", "/effects/1"])],
        facets={"level": 1, "school": "abjuration", "classes": ["sorcerer", "wizard"], "concentration": False,
                "ritual": False},
        data={"casting_time": {"cost": "reaction",
                               "triggers": [{"event": "hit_by_attack_roll", "whose": "self"},
                                            {"event": "targeted_by_spell.magic-missile", "whose": "self"}]},
              "range": {"kind": "self"}, "components": {"verbal": True, "somatic": True},
              "duration": {"kind": "rounds", "amount": 1, "text": "1 round"}},
        effects=[{"op": "modifier", "stat": "ac", "mode": "add", "value": 5, "target": {"kind": "self"},
                  "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "self"}},
                  "note": "Applies against the triggering attack."},
                 {"op": "modifier", "stat": "damage_taken.magic-missile", "mode": "set", "value": 0,
                  "target": {"kind": "self"},
                  "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "self"}}}])
    dump("catalog_entry.spell-shield", e)

    # homebrew: same schema, derived from an official entry; the base is never modified
    dump("catalog_entry.homebrew-fireball", {
        "$schema": "../catalog_entry.schema.json",
        "ref": "custom/table-42/spell/blue-fireball",
        "kind": "spell",
        "name": "Bola de Fogo Azul",
        "schema_version": "1.0",
        "source": {"system": "dnd5e", "document": "homebrew", "origin": "homebrew", "owner": "table-42",
                   "license": {"id": "homebrew"}},
        "tier": 2,
        "extends": "dnd5e/spell/fireball",
        "overrides": {"effects": [{"op": "save", "ability": "dex", "dc": {"var": "spell_save_dc"},
                                   "target": fireball_target,
                                   "on_fail": [{"op": "damage", "amount": upcast(8, 3, 6), "damage_type": "cold"}],
                                   "half_on_success": True}]},
        "effects": [{"op": "save", "ability": "dex", "dc": {"var": "spell_save_dc"}, "target": fireball_target,
                     "on_fail": [{"op": "damage", "amount": upcast(8, 3, 6), "damage_type": "cold"}],
                     "half_on_success": True}],
        "coverage": [],
    })

    # system: an excerpt of the real dnd5e system (two items per list), kept valid
    system = json.loads((ROOT / "knowledge" / "dnd5e" / "system.json").read_text(encoding="utf-8"))

    def trim(o):
        if isinstance(o, list):
            return [trim(x) for x in o[:2]]
        if isinstance(o, dict):
            return {k: trim(v) for k, v in o.items()}
        return o
    excerpt = trim(system)
    excerpt["$schema"] = "../system.schema.json"
    excerpt["registries"] = system["registries"]  # registries are kept whole: they close the vocabulary
    dump("system", excerpt)
    print("examples written")


if __name__ == "__main__":
    main()
