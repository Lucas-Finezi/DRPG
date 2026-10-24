#!/usr/bin/env python3
"""L06 — Damage, healing, Hit Points, death and stabilization, damage types, Resistance,
Vulnerability, Immunity, Temporary Hit Points, and the five hazards.

Usage: python3 -I tools/build/l06_damage.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, extend_registries, glossary, md, ref_of, section, write_entry  # noqa: E402

LOT = "L06"
SYS = "dnd5e/system/dnd5e"
C = lambda slug: f"dnd5e/condition/{slug}"  # noqa: E731
DH = "dnd5e/rule/damage-and-healing"

REGISTRY = {
    "variables": [
        {"id": "hp", "description": "Current Hit Points.", "type": "number", "pages": [16]},
        {"id": "temp_hp", "description": "Current Temporary Hit Points.", "type": "number", "pages": [18]},
        {"id": "fall_feet", "description": "Distance in feet of the current fall.", "type": "number", "pages": [182]},
        {"id": "days_without_food", "description": "Consecutive days the creature has eaten nothing.", "type": "number", "pages": [185]},
    ],
    "predicates": [
        {"id": "bloodied", "description": "The creature has half its Hit Points or fewer remaining.", "type": "predicate", "pages": [16, 177]},
        {"id": "at_zero_hp", "description": "The creature has 0 Hit Points.", "type": "predicate", "pages": [17]},
        {"id": "stable", "description": "The creature is Stable.", "type": "predicate", "pages": [18, 188]},
        {"id": "is_monster", "description": "The creature is a monster (controlled by the GM).", "type": "predicate", "pages": [17]},
        {"id": "falls_into_liquid", "description": "The fall ends in water or another liquid.", "type": "predicate", "pages": [182]},
        {"id": "out_of_breath", "description": "The creature has run out of breath or is choking.", "type": "predicate", "pages": [189]},
    ],
    "events": [
        {"id": "fall_ends", "description": "A falling creature lands.", "type": "event", "pages": [182]},
        {"id": "day_ends", "description": "The end of a day (food and water needs).", "type": "event", "pages": [181, 185]},
        {"id": "damage_taken", "description": "The creature takes damage.", "type": "event", "pages": [17, 18]},
        {"id": "drops_to_0_hp", "description": "The creature drops to 0 Hit Points.", "type": "event", "pages": [17]},
    ],
    "frequencies": [
        {"id": "instance", "description": "Once per instance of damage.", "pages": [17]},
    ],
}


def g(name, items, kind="rule", **kw):
    return glossary(name, kind, LOT, items, **kw)


def glossary_entries():
    E = []
    E.append(g("Bloodied", [(None, "rule", {"id": "bloodied", "when": {"pred": "bloodied"},
                                            "threshold": "hp_at_most_half_of_max"})]))
    E.append(g("Burning", [
        (None, "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "self", "which": "each"},
                      "then": [{"op": "damage", "amount": "1d4", "damage_type": "fire"}]}),
        ("As an action, you can extinguish fire", "fx", {"op": "activation", "name": "Extinguish fire", "cost": "action",
                                                          "then": [{"op": "apply_condition", "condition": C("prone")},
                                                                   {"op": "end_effect", "scope": "this_entry"}]}),
        ("The fire also goes out", "rule", {"id": "extinguished_by", "doused": True, "submerged": True,
                                            "suffocated": True})], kind="hazard"))
    E.append(g("Damage", [(None, "rule", {"id": "damage", "reduces": "hit_points"})]))
    E.append(g("Damage Roll", [(None, "rule", {"id": "damage_roll", "dice_plus_modifiers": True}),
                               ("*See also*", "ref", [DH])]))
    E.append(g("Damage Threshold", [
        (None, "rule", {"id": "damage_threshold", "per": "single_attack_or_effect",
                        "below_threshold": "no_damage", "at_or_above_threshold": "takes_entire_instance"})]))
    E.append(g("Damage Types", [(None, "sys", [f"{SYS}#/registries/damage_types"]),
                                ("The Damage Types table offers examples", "md", md(
                                    "assign_damage_type", "Which damage type does this new effect deal?",
                                    "The Damage Types table offers examples to help a GM assign a type to a new "
                                    "effect.", pages=[180]))]))
    E.append(g("Dead", [
        (None, "rule", {"id": "dead", "hit_points": 0, "regains_hp": False,
                        "revival": ["dnd5e/spell/raise-dead", "dnd5e/spell/revivify"]}),
        ("When such a spell is cast, the spirit knows", "md", md("spirit_refuses", "Does the dead creature's spirit "
                                                                 "accept being revived?", "When such a spell is cast, "
                                                                 "the spirit knows who is casting it and can refuse.",
                                                                 reason="narrative", pages=[180])),
        ("The spirit of a dead creature has left the body", "desc", None),
        ("If the creature returns to life", "rule", {"id": "return_to_life", "hp_from": "revival_effect",
                                                     "keeps_ongoing": ["conditions", "magical_contagions", "curses"],
                                                     "exhaustion_levels": -1, "attunement": "ended"})]))
    E.append(g("Death Saving Throw", [(None, "ref", ["dnd5e/rule/dropping-to-0-hit-points"]),
                                      ("*See also*", "ref", [DH])]))
    E.append(g("Dehydration", [
        (None, "table", {"id": "water_needs_per_day", "caption": "Water Needs per Day", "columns": ["Size", "Water"],
                         "rows": [["Tiny", "1/4 gallon"], ["Small", "1 gallon"], ["Medium", "1 gallon"],
                                  ["Large", "4 gallons"], ["Huge", "16 gallons"], ["Gargantuan", "64 gallons"]]}),
        ("A creature that drinks less than half", "fx", {
            "op": "trigger", "event": {"event": "day_ends"},
            "note": "When the creature drank less than half the required water that day.",
            "then": [{"op": "apply_condition", "condition": C("exhaustion"), "params": {"levels": 1}}]}),
        ("Exhaustion caused by dehydration", "rule", {"id": "removal_blocked_until", "drinks_full_daily_water": True}),
        ("*See also*", "ref", [C("exhaustion")])], kind="hazard"))
    fall_dmg = {"dice": {"count": {"op": "min", "args": [20, {"op": "div", "args": [{"var": "fall_feet"}, 10]}]},
                         "faces": 6}}
    E.append(g("Falling", [
        (None, "fx", {"op": "trigger", "event": {"event": "fall_ends"}, "then": [
            {"op": "damage", "amount": fall_dmg, "damage_type": "bludgeoning"},
            {"op": "apply_condition", "condition": C("prone"), "note": "Unless the creature took no damage from the fall."}]}),
        ("A creature that falls into water", "fx", {
            "op": "trigger", "event": {"event": "fall_ends"}, "cost": "reaction", "optional": True,
            "condition": {"pred": "falls_into_liquid"},
            "then": [{"op": "check", "ability": {"choose_from": ["str", "dex"]},
                      "skill": {"choose_from": ["athletics", "acrobatics"]}, "dc": 15,
                      "on_success": [{"op": "modifier", "stat": "damage_taken", "mode": "multiply", "value": 0.5,
                                      "note": "Fall damage is halved."}]}]})], kind="hazard"))
    E.append(g("Hazard", [(None, "ref", [ref_of(n, "hazard") for n in ("Burning", "Dehydration", "Falling",
                                                                         "Malnutrition", "Suffocation")])]))
    E.append(g("Healing", [(None, "rule", {"id": "healing", "restores": "hit_points"}),
                           ("*See also*", "ref", [DH])]))
    E.append(g("Hit Points", [
        (None, "rule", {"id": "hit_points", "min": 0, "max": {"var": "hp_max"}}),
        ("*See also*", "ref", [ref_of("Breaking Objects"), DH])]))
    E.append(g("Immunity", [(None, "rule", {"id": "immunity", "damage_type": "no_damage", "condition": "not_affected"})]))
    E.append(g("Malnutrition", [
        (None, "table", {"id": "food_needs_per_day", "caption": "Food Needs per Day", "columns": ["Size", "Food"],
                         "rows": [["Tiny", "1/4 pound"], ["Small", "1 pound"], ["Medium", "1 pound"],
                                  ["Large", "4 pounds"], ["Huge", "16 pounds"], ["Gargantuan", "64 pounds"]]}),
        ("A creature that eats but consumes less than half", "fx", {
            "op": "trigger", "event": {"event": "day_ends"},
            "note": "When the creature ate, but less than half the required food that day.",
            "then": [{"op": "save", "ability": "con", "dc": 10, "on_fail": [
                {"op": "apply_condition", "condition": C("exhaustion"), "params": {"levels": 1}}]}]}),
        ("A creature that eats nothing for 5 days", "rule", {"id": "starvation", "after_days_without_food": 5,
                                                             "exhaustion_per_day": 1, "automatic": True}),
        ("Exhaustion caused by malnutrition", "rule", {"id": "removal_blocked_until", "eats_full_daily_food": True}),
        ("*See also*", "ref", [C("exhaustion")])], kind="hazard"))
    E.append(g("Resistance", [(None, "rule", {"id": "resistance", "multiplier": 0.5, "round": "down",
                                              "per_instance": 1}),
                              ("*See also*", "ref", [DH])]))
    E.append(g("Stable", [(None, "rule", {"id": "stable", "hit_points": 0, "death_saving_throws": False}),
                          ("*See also*", "ref", [DH])]))
    E.append(g("Suffocation", [
        (None, "rule", {"id": "hold_breath", "minutes": {"op": "add", "args": [1, {"var": "ability_mod.con"}]},
                        "minimum_seconds": 30}),
        ("When a creature runs out of breath", "fx", {
            "op": "trigger", "event": {"event": "turn_end", "whose": "self", "which": "each"},
            "condition": {"pred": "out_of_breath"},
            "then": [{"op": "apply_condition", "condition": C("exhaustion"), "params": {"levels": 1}}]}),
        ("When a creature can breathe again", "rule", {"id": "recover", "removes": "exhaustion_levels_from_suffocation"})],
        kind="hazard"))
    E.append(g("Temporary Hit Points", [(None, "ref", ["dnd5e/rule/playing-the-game-temporary-hit-points"]),
                                        ("*See also*", "ref", [DH])]))
    E.append(g("Vulnerability", [(None, "rule", {"id": "vulnerability", "multiplier": 2, "per_instance": 1}),
                                 ("*See also*", "ref", [DH])]))
    return E


def sections():
    E = []
    path = "Playing the Game/Damage and Healing"
    sec = lambda slug, title, items, level=3, **kw: build(  # noqa: E731
        "rule", slug, title, section(title, level, page=kw.pop("page", None)), LOT,
        path if level == 2 else f"{path}/{title}", items, **kw)

    E.append(build("rule", "damage-and-healing", "Damage and Healing",
                   section("Damage and Healing", 2, stop_titles=("Hit Points",)), LOT, path, [(None, "desc", None)],
                   data={"sections": [f"dnd5e/rule/{s}" for s in (
                       "playing-the-game-hit-points", "damage-rolls", "critical-hits", "saving-throws-and-damage",
                       "playing-the-game-damage-types", "resistance-and-vulnerability", "playing-the-game-immunity",
                       "playing-the-game-healing", "dropping-to-0-hit-points",
                       "playing-the-game-temporary-hit-points")]}))
    E.append(sec("playing-the-game-hit-points", "Hit Points", [
        (None, "rule", {"id": "range", "min": 0, "max": {"var": "hp_max"}}),
        ("Whenever you take damage, subtract it", "rule", {"id": "damage_subtracts", "no_effect_until_0": True}),
        ("If you have half your Hit Points or fewer", "ref", [ref_of("Bloodied")])], page=16))
    E.append(sec("damage-rolls", "Damage Rolls", [
        (None, "rule", {"id": "damage_roll", "minimum": 0}),
        ("When attacking with a weapon", "rule", {"id": "ability_modifier", "weapon_attack": "add_attack_ability_modifier",
                                                  "spell": "as_spell_specifies",
                                                  "fixed_damage": "no_ability_modifier_unless_stated"})], page=16))
    E.append(sec("critical-hits", "Critical Hits", [
        (None, "rule", {"id": "critical_damage", "damage_dice": "roll_twice", "modifiers": "add_once",
                        "includes_extra_dice": True})], page=16))
    E.append(sec("saving-throws-and-damage", "Saving Throws and Damage", [
        (None, "desc", None),
        ("#### Damage against Multiple Targets", "rule", {"id": "roll_once", "multiple_targets": "single_damage_roll"}),
        ("#### Half Damage", "rule", {"id": "half_damage", "multiplier": 0.5, "round": "down",
                                      "of": "damage_on_failed_save"})], page=16))
    E.append(sec("playing-the-game-damage-types", "Damage Types", [
        (None, "sys", [f"{SYS}#/registries/damage_types"])], page=16))
    E.append(sec("resistance-and-vulnerability", "Resistance and Vulnerability", [
        (None, "ref", [ref_of("Resistance"), ref_of("Vulnerability")]),
        ("#### No Stacking", "rule", {"id": "no_stacking", "instances_per_damage_type": 1}),
        ("#### Order of Application", "rule", {"id": "order", "sequence": ["adjustments", "resistance",
                                                                           "vulnerability"]})], page=17))
    E.append(sec("playing-the-game-immunity", "Immunity", [(None, "ref", [ref_of("Immunity")])], page=17))
    E.append(sec("playing-the-game-healing", "Healing", [
        (None, "ref", ["dnd5e/spell/cure-wounds", "dnd5e/magic-item/potions-of-healing",
                       ref_of("Short Rest"), ref_of("Long Rest")]),
        ("When you receive healing", "rule", {"id": "healing_cap", "max": {"var": "hp_max"}, "excess": "lost"})],
        page=17))
    E.append(sec("dropping-to-0-hit-points", "Dropping to 0 Hit Points", [
        (None, "desc", None),
        ("***Monster Death.***", "rule", {"id": "monster_death", "when": {"pred": "is_monster"}, "dies_at_0_hp": True}),
        ("***Monster Death.***", "md", md("monster_as_character", "Treat this monster like a character at 0 Hit "
                                          "Points (no instant death)?", "a Game Master can ignore this rule for an "
                                          "individual monster and treat it like a character.", when="on_gain",
                                          pages=[17])),
        ("***Hit Point Maximum of 0.***", "rule", {"id": "hp_max_zero", "dies": True}),
        ("***Massive Damage.***", "rule", {"id": "massive_damage", "dies_if_remaining_damage_at_least": {"var": "hp_max"}}),
        ("#### Character Demise", "ref", ["dnd5e/spell/raise-dead", ref_of("Dead")]),
        ("Or talk with the GM about making a new character", "md", md(
            "new_character", "Will the player make a new character to join the group?",
            "Or talk with the GM about making a new character to join the group.", reason="narrative", pages=[17])),
        ("#### Falling Unconscious", "fx", {"op": "trigger", "event": {"event": "drops_to_0_hp"},
                                            "condition": {"not": {"pred": "is_monster"}},
                                            "then": [{"op": "apply_condition", "condition": C("unconscious"),
                                                      "duration": {"kind": "while", "while": {
                                                          "pred": "hp_is", "args": {"zero": True}}},
                                                      "note": "Until the creature regains any Hit Points."}]}),
        ("#### Death Saving Throws", "rule", {"id": "death_saves", "when": "turn_start_at_0_hp", "ability": None,
                                              "roll": "1d20", "success_at_least": 10}),
        ("***Three Successes/Failures.***", "rule", {"id": "three", "successes_to_stable": 3, "failures_to_die": 3,
                                                     "consecutive": False,
                                                     "reset_on": ["regain_hit_points", "become_stable"]}),
        ("***Rolling a 1 or 20.***", "rule", {"id": "natural", "natural_1": "two_failures",
                                              "natural_20": "regain_1_hit_point"}),
        ("***Damage at 0 Hit Points.***", "rule", {"id": "damage_at_0", "any_damage": "one_failure",
                                                   "critical_hit": "two_failures",
                                                   "dies_if_damage_at_least": {"var": "hp_max"}}),
        ("#### Stabilizing a Character", "fx", {"op": "activation", "name": "Stabilize", "cost": "action",
                                                "then": [{"op": "check", "ability": "wis", "skill": "medicine", "dc": 10,
                                                          "target": {"kind": "creature", "filter": {
                                                              "predicate": {"pred": "at_zero_hp"}}},
                                                          "on_success": [{"op": "reference",
                                                                          "rule": ref_of("Stable")}]}]}),
        ("A Stable creature doesn’t make Death Saving Throws", "rule", {
            "id": "stable", "death_saves": False, "keeps": C("unconscious"), "damage_ends_stable": True,
            "regain_1_hp_after": {"dice": "1d4", "unit": "hours"}})], page=17))
    E.append(sec("playing-the-game-temporary-hit-points", "Temporary Hit Points", [
        (None, "rule", {"id": "buffer", "temp_hp_are_not_hp": True}),
        ("#### Lose Temporary Hit Points First", "rule", {"id": "lost_first", "overflow": "to_hit_points"}),
        ("#### Duration", "rule", {"id": "duration", "until": ["depleted", "long_rest_finished"]}),
        ("#### They Don’t Stack", "rule", {"id": "no_stacking", "on_new": "choose_keep_or_replace"}),
        ("#### They’re Not Hit Points or Healing", "rule", {"id": "not_healing", "added_to_hp": False,
                                                           "restored_by_healing": False, "counts_as_healing": False,
                                                           "at_0_hp_restores_consciousness": False})], page=18))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = glossary_entries() + sections()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
