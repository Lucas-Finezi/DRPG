#!/usr/bin/env python3
"""L14 (part) — Paladin and Oath of Devotion features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, active, col, spell_table, spellcasting  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
P = "Paladin"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
CHA = {"var": "ability_mod.cha"}
CHA1 = {"op": "max", "args": [1, CHA]}
CD = {"resource": "channel_divinity", "amount": 1}
STYLES = ["dnd5e/feat/archery", "dnd5e/feat/defense", "dnd5e/feat/great-weapon-fighting",
          "dnd5e/feat/two-weapon-fighting"]
IN_AURA = {"pred": "in_aura", "args": {"aura": "paladin-aura-of-protection"}}
AURA_AREA = {"kind": "area", "area": {"shape": "emanation", "size_feet": {"var": "aura_size.paladin-aura-of-protection"},
                                      "origin": "self"}, "filter": {"allies_only": True}}


def entries():
    E = []
    E.append(CF(P, "Lay On Hands", 1, [
        (None, "fx", {"op": "resource", "resource": "lay_on_hands", "name": "Lay On Hands",
                      "max": {"op": "mul", "args": [5, {"var": "class_level.paladin"}]},
                      "recovery": [{"on": LONG, "amount": "all"}]}),
        ("As a Bonus Action, you can touch a creature", "fx", {
            "op": "activation", "name": "Lay On Hands", "cost": "bonus_action",
            "uses": {"resource": "lay_on_hands", "amount": {"var": "chosen.lay_on_hands_points"}},
            "target": {"kind": "creature", "range": {"kind": "touch"}}, "note": "The creature can be yourself.",
            "then": [{"op": "heal", "amount": {"var": "chosen.lay_on_hands_points"}}]}),
        ("You can also expend 5 Hit Points from the pool", "fx", {
            "op": "activation", "name": "Lay On Hands: cure poison", "cost": "bonus_action",
            "uses": {"resource": "lay_on_hands", "amount": 5}, "target": {"kind": "creature", "range": {"kind": "touch"}},
            "then": [{"op": "remove_condition", "conditions": [C("poisoned")]}]})]))
    E.append(CF(P, "Spellcasting", 1, spellcasting(
        P, "cha", ["dnd5e/gear/holy-symbol"], 2, ["Heroism", "Searing Smite"], "long_rest_one")))
    E.append(CF(P, "Weapon Mastery", 1, [
        (None, "fx", {"op": "modifier", "stat": "weapon_mastery_kinds", "mode": "set", "value": 2,
                      "note": "Kinds of weapons you are proficient with."}),
        ("Whenever you finish a Long Rest", "rule", {"id": "choices", "weapons": "proficient", "swap_on_long_rest": "all"})]))
    E.append(CF(P, "Fighting Style", 2, [
        (None, "fx", {"op": "choice", "id": "fighting_style", "choose": 1, "options": [
            {"id": "feat", "label": "Fighting Style feat", "effects": [{"op": "grant", "refs": STYLES, "choose": 1}]},
            {"id": "blessed_warrior", "label": "Blessed Warrior", "effects": [
                {"op": "grant", "refs": ["dnd5e/spell-list/cleric"], "choose": 2,
                 "note": "Two Cleric cantrips; Guidance and Sacred Flame are recommended."}]}]}),
        ("***Blessed Warrior.***", "rule", {"id": "blessed_warrior", "cantrips": 2, "from": "dnd5e/spell-list/cleric",
                                           "recommended": ["dnd5e/spell/guidance", "dnd5e/spell/sacred-flame"],
                                           "count_as": "dnd5e/class/paladin", "ability": "cha",
                                           "replace": {"on": "level_gained", "count": 1}})]))
    E.append(CF(P, "Paladin’s Smite", 2, [(None, "fx", [
        {"op": "grant", "refs": ["dnd5e/spell/divine-smite"], "note": "Always prepared."},
        {"op": "activation", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
         "then": [{"op": "cast_spell", "spell": "dnd5e/spell/divine-smite", "slot": "none"}],
         "note": "Casting time as normal for the spell."}])]))
    E.append(CF(P, "Channel Divinity", 3, [
        (None, "rule", {"id": "channel_divinity", "effects": ["divine_sense"], "one_effect_per_use": True}),
        ("You can use this class’s Channel Divinity twice.", "fx", {
            "op": "resource", "resource": "channel_divinity", "name": "Channel Divinity", "max": col(P, "Channel Divinity"),
            "recovery": [{"on": SHORT, "amount": 1}, {"on": LONG, "amount": "all"}]}),
        ("If a Channel Divinity effect requires a saving throw", "rule", {"id": "save_dc", "dc": "spell_save_dc"}),
        ("***Divine Sense.***", "fx", {
            "op": "activation", "name": "Divine Sense", "cost": "bonus_action", "uses": CD,
            "then": [{"op": "sense", "sense": "divine_sense", "range_feet": 60,
                      "duration": {"kind": "minutes", "amount": 10},
                      "note": "Location and type of Celestials, Fiends and Undead; consecrated or desecrated places and objects, as with Hallow. Ends early if Incapacitated."}]})]))
    E.append(CF(P, "Paladin Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/oath-of-devotion"], "choose": 1,
        "note": "Gain each subclass feature of your Paladin level or lower."})]))
    E.append(CF(P, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Paladin levels 8, 12 and 16."})]))
    E.append(CF(P, "Extra Attack", 5, [(None, "fx", {"op": "modifier", "stat": "attacks_per_attack_action",
                                                       "mode": "max", "value": 2})]))
    E.append(CF(P, "Faithful Steed", 5, [
        (None, "fx", {"op": "grant", "refs": ["dnd5e/spell/find-steed"], "note": "Always prepared."}),
        ("You can also cast the spell once", "fx", {
            "op": "activation", "cost": "none", "frequency": {"count": 1, "per": "long_rest"},
            "then": [{"op": "cast_spell", "spell": "dnd5e/spell/find-steed", "slot": "none"}]})]))
    E.append(CF(P, "Aura of Protection", 6, [
        (None, "fx", {"op": "modifier", "stat": "aura_size.paladin-aura-of-protection", "mode": "max", "value": 10,
                      "when": {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}}}),
        ("You and your allies in the aura", "fx", {
            "op": "modifier", "stat": "saving_throw", "mode": "add", "value": CHA1, "target": AURA_AREA,
            "when": {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}}}),
        ("If another Paladin is present", "rule", {"id": "one_aura", "max_auras_of_protection": 1,
                                                    "chooser": "affected_creature"})]))
    E.append(CF(P, "Abjure Foes", 9, [
        (None, "fx", {"op": "activation", "name": "Abjure Foes", "cost": "action", "action": "dnd5e/action/magic",
                      "uses": CD,
                      "then": [{"op": "save", "ability": "wis", "dc": {"var": "spell_save_dc"},
                                "target": {"kind": "creature", "count": {"op": "max", "args": [1, CHA]},
                                           "range": {"kind": "distance", "feet": 60}, "must_see": True},
                                "on_fail": [{"op": "apply_condition", "condition": C("frightened"),
                                             "duration": {"kind": "minutes", "amount": 1},
                                             "note": "Ends early if the target takes any damage."},
                                            {"op": "restrict", "restrictions": ["more_than_one_of_move_action_bonus_action"],
                                             "duration": {"kind": "minutes", "amount": 1}}]}]}),
        ("While Frightened in this way", "sys", ["/effects/0/then/0/on_fail/1"])]))
    E.append(CF(P, "Aura of Courage", 10, [(None, "fx", {
        "op": "defense", "kind": "immunity", "conditions": [C("frightened")], "target": AURA_AREA,
        "note": "A Frightened ally entering the aura: the condition has no effect there."})]))
    E.append(CF(P, "Radiant Strikes", 11, [(None, "fx", {
        "op": "trigger", "event": {"event": "hits_with_attack_roll"},
        "condition": {"any": [{"pred": "attack_with_melee_weapon"}, {"pred": "attack_is_unarmed_strike"}]},
        "then": [{"op": "damage", "amount": "1d8", "damage_type": "radiant", "target": {"kind": "inherit"}}]})]))
    E.append(CF(P, "Restoring Touch", 14, [(None, "fx", {
        "op": "trigger", "event": {"event": "uses_feature.paladin-lay-on-hands"}, "optional": True,
        "then": [{"op": "repeat", "times": {"var": "chosen.conditions_removed"}, "then": [
            {"op": "spend", "resource": "lay_on_hands", "amount": 5},
            {"op": "remove_condition", "count": 1, "target": {"kind": "inherit"},
             "conditions": [C(c) for c in ("blinded", "charmed", "deafened", "frightened", "paralyzed", "stunned")]}]}],
        "note": "Those points don't also restore Hit Points."})]))
    E.append(CF(P, "Aura Expansion", 18, [(None, "fx", {
        "op": "modifier", "stat": "aura_size.paladin-aura-of-protection", "mode": "max", "value": 30})]))
    E.append(CF(P, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-truesight"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Truesight is recommended."})]))

    S = "Oath of Devotion"
    rows = spell_table("Oath of Devotion Spells")
    E.append(CF(P, "Oath of Devotion Spells", 3, [
        (None, "fx", [{"op": "grant", "refs": r["spells"], "note": "Always prepared.",
                       "when": {"pred": "class_level_at_least", "args": {"class": "paladin", "level": r["level"]}}}
                      for r in rows]),
        ("##### Oath of Devotion Spells", "ref", ["dnd5e/spell-list/oath-of-devotion-spells"]),
        ("##### Oath of Devotion Spells", "table", {
            "id": "oath_of_devotion_spells", "caption": "Oath of Devotion Spells", "columns": ["Paladin Level", "Spells"],
            "rows": [[r["level"], r["spells"]] for r in rows]})], sub=S))
    E.append(CF(P, "Sacred Weapon", 3, [
        (None, "fx", {"op": "trigger", "event": {"event": "takes_attack_action"}, "optional": True,
                      "condition": {"pred": "holds_melee_weapon"},
                      "then": [{"op": "spend", "resource": "channel_divinity", "amount": 1},
                               {"op": "modifier", "stat": "attack_roll", "mode": "add", "value": CHA1,
                                "when": {"pred": "attack_with_chosen_weapon"},
                                "duration": {"kind": "minutes", "amount": 10}}]}),
        (None, "rule", {"id": "damage_type", "choose_from": ["normal_damage_type", "radiant"], "on": "each_hit"}),
        ("The weapon also emits Bright Light", "rule", {"id": "light", "bright_feet": 20, "dim_feet": 20}),
        ("You can end this effect early", "rule", {"id": "ends", "ends_on": ["used_again", "not_carrying_weapon"],
                                                   "end_early_cost": "none"})], sub=S))
    E.append(CF(P, "Aura of Devotion", 7, [(None, "fx", {
        "op": "defense", "kind": "immunity", "conditions": [C("charmed")], "target": AURA_AREA,
        "note": "A Charmed ally entering the aura: the condition has no effect there."})], sub=S))
    E.append(CF(P, "Smite of Protection", 15, [(None, "fx", {
        "op": "trigger", "event": {"event": "casts_spell.divine-smite"},
        "then": [{"op": "reference", "rule": "dnd5e/rule/cover", "target": AURA_AREA,
                  "note": "Half Cover while in your Aura of Protection.",
                  "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "self"}}}]})], sub=S))
    E.append(CF(P, "Holy Nimbus", 20, [
        (None, "fx", [
            {"op": "activation", "name": "Holy Nimbus", "cost": "bonus_action",
             "frequency": {"count": 1, "per": "long_rest"},
             "then": [{"op": "reference", "rule": "dnd5e/feature/oath-of-devotion-holy-nimbus",
                       "duration": {"kind": "minutes", "amount": 10}, "note": "Benefits below; end at will (no action)."}]},
            {"op": "activation", "name": "Restore Holy Nimbus", "cost": "none",
             "uses": {"resource": "spell_slot", "amount": 1},
             "then": [{"op": "reference", "rule": "dnd5e/feature/oath-of-devotion-holy-nimbus",
                       "note": "Regain the use; requires a level 5 spell slot."}]}]),
        ("***Holy Ward.***", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw"],
                                   "when": {"all": [active("oath-of-devotion-holy-nimbus"),
                                                    {"any": [{"pred": "forced_by_creature_type", "args": {"type": "fiend"}},
                                                             {"pred": "forced_by_creature_type", "args": {"type": "undead"}}]}]}}),
        ("***Radiant Damage.***", "fx", {
            "op": "trigger", "event": {"event": "turn_start", "whose": "target"},
            "condition": {"all": [active("oath-of-devotion-holy-nimbus"), {"pred": "is_enemy"}, IN_AURA]},
            "then": [{"op": "damage", "damage_type": "radiant", "target": {"kind": "inherit"},
                      "amount": {"op": "add", "args": [CHA, {"var": "proficiency_bonus"}]}}]}),
        ("***Sunlight.***", "rule", {"id": "sunlight", "aura_light": "bright", "is_sunlight": True})], sub=S))
    return E


REGISTRY = {
    "variables": [{"id": "aura_size", "description": "Size in feet of a creature's aura (param: feature slug).", "params": ["feature"], "type": "number", "pages": [55]}],
    "stats": [{"id": "aura_size", "description": "Size in feet of a creature's aura (param: feature slug).", "params": ["feature"], "pages": [55]}],
    "senses": [{"id": "divine_sense", "description": "Knows the location and type of Celestials, Fiends and Undead, and consecrated or desecrated places and objects, within range.", "pages": [54]}],
    "restrictions": [{"id": "more_than_one_of_move_action_bonus_action", "description": "On its turns, can do only one of: move, take an action, or take a Bonus Action.", "pages": [55]}],
    "events": [{"id": "casts_spell", "description": "The creature casts a spell (param: spell slug).", "params": ["spell"], "pages": [57]}],
    "predicates": [
        {"id": "in_aura", "description": "The creature is inside the source's aura (param: feature slug).", "params": ["aura"], "type": "predicate", "pages": [55]},
        {"id": "attack_with_melee_weapon", "description": "The attack roll uses a Melee weapon.", "type": "predicate", "pages": [55]},
        {"id": "holds_melee_weapon", "description": "The creature holds a Melee weapon.", "type": "predicate", "pages": [56]},
        {"id": "attack_with_chosen_weapon", "description": "The attack uses the weapon chosen for the effect.", "type": "predicate", "pages": [56]},
        {"id": "forced_by_creature_type", "description": "The saving throw is forced by a creature of this type (param).", "params": ["type"], "type": "predicate", "pages": [57]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
