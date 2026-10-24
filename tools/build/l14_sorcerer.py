#!/usr/bin/env python3
"""L14 (part) — Sorcerer, Metamagic options and Draconic Sorcery features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, OPT, active, col, spell_table, spellcasting  # noqa: E402
from entrylib import extend_registries, table_nodes, write_entry  # noqa: E402

LOT = "L14"
S_ = "Sorcerer"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
CHA = {"var": "ability_mod.cha"}
CHA1 = {"op": "max", "args": [1, CHA]}
SP = lambda n: {"resource": "sorcery_points", "amount": n}  # noqa: E731
INNATE = active("sorcerer-innate-sorcery")
MM = "Metamagic Options"


def meta(name, cost, items):
    """A Metamagic option: its cost line, then the option's own items."""
    return OPT(S_, name, "metamagic_option", MM, [
        (None, "rule", {"id": "cost", "resource": "sorcery_points", "amount": cost})] + items)


def entries():
    E = []
    E.append(CF(S_, "Spellcasting", 1, spellcasting(
        S_, "cha", ["dnd5e/gear/arcane-focus"], 2, ["Burning Hands", "Detect Magic"], "level_gain_one",
        cantrips=(4, ["Light", "Prestidigitation", "Shocking Grasp", "Sorcerous Burst"], "level_gained"))))
    E.append(CF(S_, "Innate Sorcery", 1, [
        (None, "fx", {"op": "activation", "name": "Innate Sorcery", "cost": "bonus_action",
                      "uses": {"resource": "innate_sorcery", "amount": 1},
                      "then": [{"op": "modifier", "stat": "spell_save_dc", "mode": "add", "value": 1,
                                "when": {"pred": "spell_of_class", "args": {"class": "sorcerer"}},
                                "duration": {"kind": "minutes", "amount": 1}},
                               {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                                "when": {"pred": "spell_of_class", "args": {"class": "sorcerer"}},
                                "duration": {"kind": "minutes", "amount": 1}}]}),
        ("- The spell save DC", "sys", ["/effects/0/then/0"]),
        ("- You have Advantage", "sys", ["/effects/0/then/1"]),
        ("You can use this feature twice", "fx", {"op": "resource", "resource": "innate_sorcery", "max": 2,
                                                  "recovery": [{"on": LONG, "amount": "all"}]})]))
    slots = [n.cells for n in table_nodes("Creating Spell Slots")[1:] if n.type == "t" and not n.text.startswith("| **")]
    E.append(CF(S_, "Font of Magic", 2, [
        (None, "desc", None),
        ("You have 2 Sorcery Points", "fx", {"op": "resource", "resource": "sorcery_points", "name": "Sorcery Points",
                                             "max": col(S_, "Sorcery Points"),
                                             "recovery": [{"on": LONG, "amount": "all"}]}),
        ("You can use your Sorcery Points to fuel", "desc", None),
        ("***Converting Spell Slots to Sorcery Points.***", "fx", {
            "op": "activation", "cost": "none", "uses": {"resource": "spell_slot", "amount": 1},
            "then": [{"op": "restore", "resource": "sorcery_points", "amount": {"var": "spell_slot_level"},
                      "note": "Cannot exceed the Sorcery Points maximum."}]}),
        ("***Creating Spell Slots.***", "fx", {
            "op": "activation", "cost": "bonus_action",
            "uses": SP({"table": "dnd5e/feature/sorcerer-font-of-magic", "table_id": "creating_spell_slots",
                        "key": {"var": "chosen.slot_level"}, "column": "Sorcery Point Cost"}),
            "then": [{"op": "restore", "resource": "spell_slot", "amount": 1, "level": {"var": "chosen.slot_level"},
                      "note": "Max level 5; minimum Sorcerer level per the table; vanishes after a Long Rest."}]}),
        ("Any spell slot you create", "rule", {"id": "created_slots_vanish", "on": "long_rest_finished"}),
        ("##### Creating Spell Slots", "table", {
            "id": "creating_spell_slots", "caption": "Creating Spell Slots",
            "columns": ["Spell Slot Level", "Sorcery Point Cost", "Min. Sorcerer Level"], "rows": slots})]))
    E.append(CF(S_, "Metamagic", 2, [
        (None, "rule", {"id": "metamagic", "options_known": {"scale": {"by": "class_level.sorcerer", "steps": [
            {"from": 2, "value": 2}, {"from": 10, "value": 4}, {"from": 17, "value": 6}]}},
                        "from": "feature_type:metamagic_option", "cost": "sorcery_points"}),
        ("You can use only one Metamagic option", "rule", {"id": "one_per_spell", "max_options_per_spell": 1,
                                                           "unless_option_says_otherwise": True}),
        ("Whenever you gain a Sorcerer level", "rule", {"id": "replace", "on": "level_gained", "count": 1})]))
    E.append(CF(S_, "Sorcerer Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/draconic-sorcery"], "choose": 1,
        "note": "Gain each subclass feature of your Sorcerer level or lower."})]))
    E.append(CF(S_, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Sorcerer levels 8, 12 and 16."})]))
    E.append(CF(S_, "Sorcerous Restoration", 5, [(None, "fx", {
        "op": "trigger", "event": SHORT, "optional": True, "frequency": {"count": 1, "per": "long_rest"},
        "then": [{"op": "restore", "resource": "sorcery_points",
                  "amount": {"op": "div", "args": [{"var": "class_level.sorcerer"}, 2]}}]})]))
    E.append(CF(S_, "Sorcery Incarnate", 7, [
        (None, "fx", {"op": "activation", "name": "Innate Sorcery (Sorcery Points)", "cost": "bonus_action",
                      "requires": {"pred": "resource_empty", "args": {"resource": "innate_sorcery"}}, "uses": SP(2),
                      "then": [{"op": "reference", "rule": "dnd5e/feature/sorcerer-innate-sorcery"}]}),
        ("In addition, while your Innate Sorcery", "rule", {"id": "two_metamagic", "when": "innate_sorcery_active",
                                                            "max_options_per_spell": 2})]))
    E.append(CF(S_, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-dimensional-travel"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Dimensional Travel is recommended."})]))
    E.append(CF(S_, "Arcane Apotheosis", 20, [(None, "rule", {
        "id": "free_metamagic", "when": "innate_sorcery_active", "per": "turn", "count": 1, "cost": 0})]))

    E.append(meta("Careful Spell", 1, [("When you cast a spell that forces", "fx", {
        "op": "trigger", "event": {"event": "casts_spell_forcing_save"}, "optional": True,
        "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                 {"op": "auto_result", "rolls": ["saving_throw"], "result": "success",
                  "target": {"kind": "creature", "count": CHA1}, "note": "Chosen creatures; no damage instead of half."}]})]))
    E.append(meta("Distant Spell", 1, [("When you cast a spell that has a range", "fx", {
        "op": "trigger", "event": {"event": "casts_spell"}, "optional": True,
        "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                 {"op": "choice", "id": "distant", "choose": 1, "options": [
                     {"id": "double", "label": "Range 5 feet or more: double", "effects": [
                         {"op": "modifier", "stat": "spell_range", "mode": "multiply", "value": 2}]},
                     {"id": "touch", "label": "Range Touch: 30 feet", "effects": [
                         {"op": "modifier", "stat": "spell_range", "mode": "set", "value": 30}]}]}]})]))
    E.append(meta("Empowered Spell", 1, [
        ("When you roll damage for a spell", "fx", {
            "op": "trigger", "event": {"event": "rolls_spell_damage"}, "optional": True,
            "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                     {"op": "reroll", "rolls": ["damage_roll"], "dice": CHA1, "keep": "new"}]}),
        ("You can use Empowered Spell even if", "rule", {"id": "stacks", "combinable_with_other_metamagic": True})]))
    E.append(meta("Extended Spell", 1, [
        ("When you cast a spell that has a duration", "fx", {
            "op": "trigger", "event": {"event": "casts_spell"}, "optional": True,
            "condition": {"pred": "spell_duration_at_least_minutes", "args": {"minutes": 1}},
            "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                     {"op": "modifier", "stat": "spell_duration", "mode": "multiply", "value": 2,
                      "note": "Maximum duration 24 hours."}]}),
        ("If the affected spell requires Concentration", "fx", {
            "op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.con"],
            "when": {"pred": "concentration_save_for_extended_spell"}})]))
    E.append(meta("Heightened Spell", 2, [("When you cast a spell that forces", "fx", {
        "op": "trigger", "event": {"event": "casts_spell_forcing_save"}, "optional": True,
        "then": [{"op": "spend", "resource": "sorcery_points", "amount": 2},
                 {"op": "roll_mode", "mode": "disadvantage", "rolls": ["saving_throw"],
                  "target": {"kind": "creature", "count": 1}, "note": "One target, on saves against the spell."}]})]))
    E.append(meta("Quickened Spell", 2, [("When you cast a spell that has a casting time", "fx", {
        "op": "trigger", "event": {"event": "casts_spell"}, "optional": True,
        "condition": {"all": [{"pred": "spell_casting_time", "args": {"time": "action"}},
                              {"not": {"pred": "cast_level_1_plus_spell_this_turn"}}]},
        "then": [{"op": "spend", "resource": "sorcery_points", "amount": 2},
                 {"op": "modifier", "stat": "spell_casting_time", "mode": "set", "value": 0,
                  "note": "Casting time becomes a Bonus Action for this casting."},
                 {"op": "restrict", "restrictions": ["cast_level_1_plus_spells"],
                  "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self"}}}]})]))
    E.append(meta("Seeking Spell", 1, [
        ("If you make an attack roll for a spell and miss", "fx", {
            "op": "trigger", "event": {"event": "misses_with_spell_attack"}, "optional": True,
            "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                     {"op": "reroll", "rolls": ["attack_roll"], "keep": "new"}]}),
        ("You can use Seeking Spell even if", "rule", {"id": "stacks", "combinable_with_other_metamagic": True})]))
    E.append(meta("Subtle Spell", 1, [("When you cast a spell, you can spend", "fx", {
        "op": "trigger", "event": {"event": "casts_spell"}, "optional": True,
        "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                 {"op": "modifier", "stat": "spell_components", "mode": "set", "value": 0,
                  "note": "No Verbal, Somatic or Material components, except consumed or costed Material components."}]})]))
    E.append(meta("Transmuted Spell", 1, [("When you cast a spell that deals a type", "fx", {
        "op": "trigger", "event": {"event": "casts_spell"}, "optional": True,
        "condition": {"any": [{"pred": "deals_damage_type", "args": {"type": t}}
                              for t in ("acid", "cold", "fire", "lightning", "poison", "thunder")]},
        "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                 {"op": "choice", "id": "new_type", "choose": 1, "options": [
                     {"id": t, "label": t.title(), "value": t, "effects": []}
                     for t in ("acid", "cold", "fire", "lightning", "poison", "thunder")],
                  "note": "Change to one of the other listed types."}]})]))
    E.append(meta("Twinned Spell", 1, [("When you cast a spell, such as", "fx", {
        "op": "trigger", "event": {"event": "casts_spell"}, "optional": True,
        "condition": {"pred": "spell_targets_more_at_higher_level"},
        "then": [{"op": "spend", "resource": "sorcery_points", "amount": 1},
                 {"op": "modifier", "stat": "spell_effective_level", "mode": "add", "value": 1}]})]))

    S = "Draconic Sorcery"
    E.append(CF(S_, "Draconic Resilience", 3, [
        (None, "fx", {"op": "modifier", "stat": "hp_max", "mode": "add",
                      "value": {"op": "add", "args": [3, {"op": "sub", "args": [{"var": "class_level.sorcerer"}, 3]}]},
                      "note": "+3, then +1 per Sorcerer level gained after this one."}),
        ("Parts of you are also covered", "fx", {
            "op": "modifier", "stat": "base_ac", "mode": "set", "when": {"not": {"pred": "wearing_armor_any"}},
            "value": {"op": "add", "args": [10, {"var": "ability_mod.dex"}, CHA]}})], sub=S))
    rows = spell_table("Draconic Spells")
    E.append(CF(S_, "Draconic Spells", 3, [
        (None, "fx", [{"op": "grant", "refs": r["spells"], "note": "Always prepared.",
                       "when": {"pred": "class_level_at_least", "args": {"class": "sorcerer", "level": r["level"]}}}
                      for r in rows]),
        ("##### Draconic Spells", "ref", ["dnd5e/spell-list/draconic-spells"]),
        ("##### Draconic Spells", "table", {"id": "draconic_spells", "caption": "Draconic Spells",
                                            "columns": ["Sorcerer Level", "Spells"],
                                            "rows": [[r["level"], r["spells"]] for r in rows]})], sub=S))
    E.append(CF(S_, "Elemental Affinity", 6, [
        (None, "fx", {"op": "choice", "id": "elemental_affinity", "choose": 1, "options": [
            {"id": t, "label": t.title(), "value": t, "effects": []}
            for t in ("acid", "cold", "fire", "lightning", "poison")]}),
        ("You have Resistance to that damage type", "fx", [
            {"op": "defense", "kind": "resistance", "damage_types": [{"var": "chosen.elemental_affinity"}]},
            {"op": "modifier", "stat": "damage_roll", "mode": "add", "value": CHA,
             "when": {"pred": "deals_damage_type", "args": {"type": "chosen.elemental_affinity"}},
             "note": "One damage roll of a spell that deals that type."}])], sub=S))
    E.append(CF(S_, "Dragon Wings", 14, [
        (None, "fx", {"op": "activation", "name": "Dragon Wings", "cost": "bonus_action",
                      "frequency": {"count": 1, "per": "long_rest"},
                      "then": [{"op": "speed", "movement": "fly", "mode": "set", "value": 60,
                                "duration": {"kind": "hours", "amount": 1}, "note": "Dismiss at will (no action)."}]}),
        ("Once you use this feature", "fx", {"op": "activation", "name": "Restore Dragon Wings", "cost": "none",
                                             "uses": SP(3),
                                             "then": [{"op": "reference", "rule": "dnd5e/feature/draconic-sorcery-dragon-wings",
                                                       "note": "Restore your use of it."}]})], sub=S))
    E.append(CF(S_, "Dragon Companion", 18, [
        (None, "fx", [{"op": "grant", "refs": ["dnd5e/spell/summon-dragon"],
                       "note": "You can cast it without a Material component."},
                      {"op": "activation", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
                       "then": [{"op": "cast_spell", "spell": "dnd5e/spell/summon-dragon", "slot": "none",
                                 "components": ["V", "S"]}]}]),
        ("Whenever you start casting the spell", "rule", {"id": "no_concentration", "spell": "dnd5e/spell/summon-dragon",
                                                          "optional": True, "concentration": False,
                                                          "duration_minutes": 1})], sub=S))
    return E


REGISTRY = {
    "stats": [
        {"id": "spell_range", "description": "Range of the spell being cast.", "pages": [67]},
        {"id": "spell_duration", "description": "Duration of the spell being cast.", "pages": [67]},
        {"id": "spell_casting_time", "description": "Casting time of the spell being cast.", "pages": [67]},
        {"id": "spell_components", "description": "Components required by the spell being cast.", "pages": [67]},
        {"id": "spell_effective_level", "description": "Effective level of the spell being cast.", "pages": [67]}],
    "restrictions": [{"id": "cast_level_1_plus_spells", "description": "The creature can't cast a level 1+ spell.", "pages": [67]}],
    "events": [
        {"id": "casts_spell_forcing_save", "description": "The creature casts a spell that forces creatures to make a saving throw.", "pages": [66]},
        {"id": "rolls_spell_damage", "description": "The creature rolls damage for a spell.", "pages": [67]},
        {"id": "misses_with_spell_attack", "description": "The creature makes an attack roll for a spell and misses.", "pages": [67]}],
    "predicates": [
        {"id": "spell_of_class", "description": "The spell is a spell of this class (param) for the creature.", "params": ["class"], "type": "predicate", "pages": [65]},
        {"id": "spell_duration_at_least_minutes", "description": "The spell's duration is at least N minutes (param).", "params": ["minutes"], "type": "predicate", "pages": [67]},
        {"id": "concentration_save_for_extended_spell", "description": "A saving throw to maintain Concentration on a spell modified by Extended Spell.", "type": "predicate", "pages": [67]},
        {"id": "spell_casting_time", "description": "The spell has this casting time (param).", "params": ["time"], "type": "predicate", "pages": [67]},
        {"id": "cast_level_1_plus_spell_this_turn", "description": "The creature has already cast a level 1+ spell this turn.", "type": "predicate", "pages": [67]},
        {"id": "spell_targets_more_at_higher_level", "description": "The spell can be cast with a higher-level slot to target an additional creature.", "type": "predicate", "pages": [67]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
