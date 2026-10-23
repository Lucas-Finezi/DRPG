#!/usr/bin/env python3
"""L14 (part) — Barbarian and Path of the Berserker features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import COMMON_REGISTRY, CF, active, col  # noqa: E402
from entrylib import extend_registries, md, write_entry  # noqa: E402

LOT = "L14"
B = "Barbarian"
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
RAGE = active("barbarian-rage")
PB = {"var": "proficiency_bonus"}
LONG = {"event": "long_rest_finished"}
NEXT_TURN_START = {"kind": "until_event", "until": {"event": "turn_start", "whose": "self"}}


def entries():
    E = []
    E.append(CF(B, "Rage", 1, [
        (None, "fx", {"op": "activation", "id": "enter_rage", "name": "Rage", "cost": "bonus_action",
                      "requires": {"not": {"pred": "wearing_armor", "args": {"category": "heavy"}}},
                      "uses": {"resource": "rage", "amount": 1},
                      "then": [{"op": "reference", "rule": "dnd5e/feature/barbarian-rage",
                                "note": "Rage becomes active (see the effects below while active)."}]}),
        ("You can enter your Rage the number of times", "fx", {
            "op": "resource", "resource": "rage", "name": "Rage", "max": col(B, "Rages"),
            "recovery": [{"on": {"event": "short_rest_finished"}, "amount": 1}, {"on": LONG, "amount": "all"}]}),
        ("While active, your Rage follows the rules below.", "desc", None),
        ("***Damage Resistance.***", "fx", {"op": "defense", "kind": "resistance",
                                           "damage_types": ["bludgeoning", "piercing", "slashing"], "when": RAGE}),
        ("***Rage Damage.***", "fx", {"op": "modifier", "stat": "damage_roll", "mode": "add", "value": col(B, "Rage Damage"),
                                     "when": {"all": [RAGE, {"pred": "attack_uses_ability", "args": {"ability": "str"}}]}}),
        ("***Strength Advantage.***", "fx", {"op": "roll_mode", "mode": "advantage",
                                            "rolls": ["ability_check.str", "saving_throw.str"], "when": RAGE}),
        ("***No Concentration or Spells.***", "fx", {"op": "restrict", "restrictions": ["maintain_concentration",
                                                                                      "cast_spells"], "when": RAGE}),
        ("***Duration.***", "rule", {"id": "duration", "lasts_until": "end_of_next_turn",
                                     "ends_early": ["don_heavy_armor", C("incapacitated")],
                                     "extend_by": ["attack_roll_against_enemy", "force_enemy_save",
                                                   "bonus_action"], "max_minutes": 10})]))
    E.append(CF(B, "Unarmored Defense", 1, [(None, "fx", {
        "op": "modifier", "stat": "base_ac", "mode": "set",
        "value": {"op": "add", "args": [10, {"var": "ability_mod.dex"}, {"var": "ability_mod.con"}]},
        "when": {"not": {"pred": "wearing_armor_any"}}, "note": "A Shield may still be used."})]))
    E.append(CF(B, "Weapon Mastery", 1, [
        (None, "fx", {"op": "modifier", "stat": "weapon_mastery_kinds", "mode": "set", "value": col(B, "Weapon Mastery"),
                      "note": "Kinds of Simple or Martial Melee weapons; one choice may change after each Long Rest."}),
        (None, "rule", {"id": "choices", "weapons": "simple_or_martial_melee", "swap_on_long_rest": 1}),
        ("When you reach certain Barbarian levels", "sys", ["/effects/0"])]))
    E.append(CF(B, "Danger Sense", 2, [(None, "fx", {
        "op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.dex"],
        "when": {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}}})]))
    E.append(CF(B, "Reckless Attack", 2, [(None, "fx", {
        "op": "trigger", "event": {"event": "attack_roll_made"}, "optional": True,
        "condition": {"pred": "first_attack_this_turn"},
        "then": [{"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                  "when": {"pred": "attack_uses_ability", "args": {"ability": "str"}}, "duration": NEXT_TURN_START},
                 {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "direction": "against",
                  "duration": NEXT_TURN_START}]})]))
    E.append(CF(B, "Barbarian Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/path-of-the-berserker"], "choose": 1,
        "note": "Gain each subclass feature of your Barbarian level or lower."})]))
    E.append(CF(B, "Primal Knowledge", 3, [
        (None, "fx", {"op": "proficiency", "category": "skill", "choose": 1,
                      "from": ["animal_handling", "athletics", "intimidation", "nature", "perception", "survival"]}),
        ("In addition, while your Rage is active", "rule", {
            "id": "strength_checks", "when": "rage_active",
            "skills": ["acrobatics", "intimidation", "perception", "stealth", "survival"], "may_use_ability": "str"})]))
    E.append(CF(B, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Barbarian levels 8, 12 and 16."})]))
    E.append(CF(B, "Extra Attack", 5, [(None, "fx", {"op": "modifier", "stat": "attacks_per_attack_action",
                                                       "mode": "max", "value": 2})]))
    E.append(CF(B, "Fast Movement", 5, [(None, "fx", {"op": "speed", "movement": "walk", "mode": "add", "value": 10,
                                                        "when": {"not": {"pred": "wearing_armor",
                                                                         "args": {"category": "heavy"}}}})]))
    E.append(CF(B, "Feral Instinct", 7, [(None, "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["initiative"]})]))
    E.append(CF(B, "Instinctive Pounce", 7, [(None, "fx", {
        "op": "trigger", "event": {"event": "enters_effect.barbarian-rage"}, "optional": True,
        "then": [{"op": "move", "mode": "move", "distance_feet": {"op": "div", "args": [{"var": "speed.walk"}, 2]}}]})]))
    brutal_opts = [
        {"id": "forceful_blow", "label": "Forceful Blow", "effects": [
            {"op": "move", "mode": "push", "distance_feet": 15, "target": {"kind": "inherit"}},
            {"op": "move", "mode": "move", "distance_feet": {"op": "div", "args": [{"var": "speed.walk"}, 2]},
             "provokes_opportunity_attacks": False, "note": "Straight toward the target (optional)."}]},
        {"id": "hamstring_blow", "label": "Hamstring Blow", "effects": [
            {"op": "speed", "movement": "walk", "mode": "add", "value": -15, "target": {"kind": "inherit"},
             "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "source"}},
             "note": "Only one Hamstring Blow at a time (the most recent)."}]}]
    E.append(CF(B, "Brutal Strike", 9, [
        (None, "fx", {"op": "trigger", "event": {"event": "attack_roll_made"}, "optional": True,
                      "condition": {"all": [active("barbarian-reckless-attack"),
                                            {"pred": "attack_uses_ability", "args": {"ability": "str"}}]},
                      "note": "Forgo Advantage on one Strength-based attack roll without Disadvantage, once per turn.",
                      "frequency": {"count": 1, "per": "turn"},
                      "then": [{"op": "attack", "attack_type": "melee", "on_hit": [
                          {"op": "damage", "amount": "1d10", "damage_type": {"var": "chosen.weapon_damage_type"},
                           "note": "Same type as the weapon or Unarmed Strike."},
                          {"op": "choice", "id": "brutal_strike_effect", "choose": 1, "options": brutal_opts}]}]}),
        ("***Forceful Blow.***", "sys", ["/effects/0/then/0/on_hit/1/options/0"]),
        ("***Hamstring Blow.***", "sys", ["/effects/0/then/0/on_hit/1/options/1"])]))
    E.append(CF(B, "Relentless Rage", 11, [
        (None, "fx", {"op": "trigger", "event": {"event": "drops_to_0_hp_not_killed"}, "optional": True,
                      "condition": RAGE,
                      "then": [{"op": "save", "ability": "con",
                                "dc": {"op": "add", "args": [10, {"op": "mul", "args": [5, {"var": "uses_since_rest.relentless_rage"}]}]},
                                "on_success": [{"op": "modifier", "stat": "hp", "mode": "set",
                                                "value": {"op": "mul", "args": [2, {"var": "class_level.barbarian"}]}}]}]}),
        ("Each time you use this feature after the first", "rule", {
            "id": "dc_escalation", "dc_increase_per_use": 5, "reset_on": ["short_rest_finished", "long_rest_finished"]})]))
    E.append(CF(B, "Improved Brutal Strike", 13, [
        (None, "rule", {"id": "new_options", "adds_options_to": "dnd5e/feature/barbarian-brutal-strike"}),
        ("***Staggering Blow.***", "fx", [
            {"op": "roll_mode", "mode": "disadvantage", "rolls": ["saving_throw"], "target": {"kind": "inherit"},
             "note": "The target's next saving throw."},
            {"op": "restrict", "restrictions": ["make_opportunity_attacks"], "target": {"kind": "inherit"},
             "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "source"}}}]),
        ("***Sundering Blow.***", "fx", {"op": "modifier", "stat": "attack_roll", "mode": "add", "value": 5,
                                        "target": {"kind": "inherit"},
                                        "note": "Next attack roll by another creature against the target before the start of your next turn; only one Sundering Blow bonus per roll."})]))
    E.append(CF(B, "Persistent Rage", 15, [
        (None, "fx", {"op": "trigger", "event": {"event": "initiative_rolled"}, "optional": True,
                      "frequency": {"count": 1, "per": "long_rest"},
                      "then": [{"op": "restore", "resource": "rage", "amount": "all"}]}),
        ("In addition, your Rage is so fierce", "rule", {"id": "persistent", "lasts_minutes": 10, "no_extension_needed": True,
                                                         "ends_early": [C("unconscious"), "don_heavy_armor"]})]))
    E.append(CF(B, "Improved Brutal Strike", 17, [(None, "rule", {
        "id": "upgrade", "brutal_strike_damage": "2d10", "effects_per_use": 2, "distinct": True})]))
    E.append(CF(B, "Indomitable Might", 18, [(None, "rule", {
        "id": "floor", "rolls": ["ability_check.str", "saving_throw.str"], "min_total": {"var": "ability_score.str"}})]))
    E.append(CF(B, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-irresistible-offense"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Irresistible Offense is recommended."})]))
    E.append(CF(B, "Primal Champion", 20, [(None, "fx", [
        {"op": "modifier", "stat": "ability_score.str", "mode": "add", "value": 4},
        {"op": "modifier", "stat": "ability_score.con", "mode": "add", "value": 4},
        {"op": "modifier", "stat": "ability_score_max.str", "mode": "max", "value": 25},
        {"op": "modifier", "stat": "ability_score_max.con", "mode": "max", "value": 25}])]))

    S = "Path of the Berserker"
    E.append(CF(B, "Frenzy", 3, [(None, "fx", {
        "op": "trigger", "event": {"event": "hits_with_attack_roll"},
        "condition": {"all": [RAGE, active("barbarian-reckless-attack"),
                              {"pred": "attack_uses_ability", "args": {"ability": "str"}}]},
        "frequency": {"count": 1, "per": "turn"},
        "then": [{"op": "damage", "amount": {"dice": {"count": col(B, "Rage Damage"), "faces": 6}},
                  "damage_type": {"var": "chosen.weapon_damage_type"}, "target": {"kind": "inherit"},
                  "note": "First target you hit on your turn; same type as the weapon or Unarmed Strike."}]})], sub=S))
    E.append(CF(B, "Mindless Rage", 6, [(None, "fx", [
        {"op": "defense", "kind": "immunity", "conditions": [C("charmed"), C("frightened")], "when": RAGE},
        {"op": "trigger", "event": {"event": "enters_effect.barbarian-rage"},
         "then": [{"op": "remove_condition", "conditions": [C("charmed"), C("frightened")]}]}])], sub=S))
    E.append(CF(B, "Retaliation", 10, [(None, "fx", {
        "op": "trigger", "event": {"event": "damaged_by_creature_within_feet.5"}, "cost": "reaction", "optional": True,
        "then": [{"op": "attack", "attack_type": "melee", "target": {"kind": "inherit"},
                  "note": "One melee attack with a weapon or an Unarmed Strike."}]})], sub=S))
    E.append(CF(B, "Intimidating Presence", 14, [
        (None, "fx", [{"op": "resource", "resource": "intimidating_presence", "max": 1,
                       "recovery": [{"on": LONG, "amount": "all"}]},
                      {"op": "activation", "name": "Intimidating Presence", "cost": "bonus_action",
                       "uses": {"resource": "intimidating_presence", "amount": 1},
                       "then": [{"op": "save", "ability": "wis",
                                 "dc": {"op": "add", "args": [8, {"var": "ability_mod.str"}, PB]},
                                 "target": {"kind": "area", "area": {"shape": "emanation", "size_feet": 30,
                                                                     "origin": "self"},
                                            "filter": {"predicate": {"pred": "chosen_by_source"}}},
                                 "on_fail": [{"op": "apply_condition", "condition": C("frightened"),
                                              "duration": {"kind": "minutes", "amount": 1}}],
                                 "repeat": {"on": {"event": "turn_end", "whose": "target", "which": "each"},
                                            "ends": "effect_on_self"}}]}]),
        ("Once you use this feature", "fx", {"op": "activation", "name": "Restore Intimidating Presence", "cost": "none",
                                             "uses": {"resource": "rage", "amount": 1},
                                             "then": [{"op": "restore", "resource": "intimidating_presence", "amount": 1}]})],
        sub=S))
    return E


REGISTRY = {
    "variables": [{"id": "uses_since_rest", "description": "Times a feature was used since the last Short or Long Rest (param).", "params": ["feature"], "type": "number", "pages": [30]}],
    "restrictions": [{"id": "make_opportunity_attacks", "description": "The creature can't make Opportunity Attacks.", "pages": [30]}],
    "predicates": [{"id": "chosen_by_source", "description": "The creature is one the source chose.", "type": "predicate", "pages": [30]}],
}

if __name__ == "__main__":
    extend_registries(COMMON_REGISTRY, LOT)
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
