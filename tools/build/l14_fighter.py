#!/usr/bin/env python3
"""L14 (part) — Fighter and Champion features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, col  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
F = "Fighter"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
STYLES = ["dnd5e/feat/archery", "dnd5e/feat/defense", "dnd5e/feat/great-weapon-fighting",
          "dnd5e/feat/two-weapon-fighting"]
HALF_SPEED = {"op": "div", "args": [{"var": "speed.walk"}, 2]}


def extra_attack(n):
    return [(None, "fx", {"op": "modifier", "stat": "attacks_per_attack_action", "mode": "max", "value": n})]


def entries():
    E = []
    E.append(CF(F, "Fighting Style", 1, [
        (None, "fx", {"op": "grant", "refs": STYLES, "choose": 1, "note": "A Fighting Style feat; Defense is recommended."}),
        ("Whenever you gain a Fighter level", "rule", {"id": "replace", "on": "level_gained",
                                                       "replace_with": "different_fighting_style_feat"})]))
    E.append(CF(F, "Second Wind", 1, [
        (None, "fx", {"op": "activation", "name": "Second Wind", "cost": "bonus_action",
                      "uses": {"resource": "second_wind", "amount": 1},
                      "then": [{"op": "heal", "amount": {"op": "add", "args": ["1d10", {"var": "class_level.fighter"}]},
                                "target": {"kind": "self"}}]}),
        ("You can use this feature twice.", "fx", {
            "op": "resource", "resource": "second_wind", "name": "Second Wind", "max": col(F, "Second Wind"),
            "recovery": [{"on": SHORT, "amount": 1}, {"on": LONG, "amount": "all"}]})]))
    E.append(CF(F, "Weapon Mastery", 1, [
        (None, "fx", {"op": "modifier", "stat": "weapon_mastery_kinds", "mode": "set", "value": col(F, "Weapon Mastery"),
                      "note": "Kinds of Simple or Martial weapons; one choice may change after each Long Rest."}),
        (None, "rule", {"id": "choices", "weapons": "simple_or_martial", "swap_on_long_rest": 1}),
        ("When you reach certain Fighter levels", "sys", ["/effects/0"])]))
    E.append(CF(F, "Action Surge", 2, [
        (None, "fx", {"op": "activation", "name": "Action Surge", "cost": "none", "requires": {"pred": "own_turn"},
                      "uses": {"resource": "action_surge", "amount": 1}, "frequency": {"count": 1, "per": "turn"},
                      "then": [{"op": "modifier", "stat": "actions_this_turn", "mode": "add", "value": 1,
                                "note": "One additional action, except the Magic action."}]}),
        ("Once you use this feature", "fx", {
            "op": "resource", "resource": "action_surge", "name": "Action Surge",
            "max": {"scale": {"by": "class_level.fighter", "steps": [{"from": 2, "value": 1}, {"from": 17, "value": 2}]}},
            "recovery": [{"on": SHORT, "amount": "all"}, {"on": LONG, "amount": "all"}]})]))
    E.append(CF(F, "Tactical Mind", 2, [(None, "fx", {
        "op": "trigger", "event": {"event": "fails_ability_check"}, "optional": True,
        "condition": {"pred": "resource_available", "args": {"resource": "second_wind"}},
        "then": [{"op": "modifier", "stat": "triggering_roll", "mode": "add", "value": "1d10"},
                 {"op": "spend", "resource": "second_wind", "amount": 1,
                  "when": {"pred": "roll_succeeded", "args": {"roll": "triggering_roll"}},
                  "note": "If the check still fails, this use of Second Wind isn't expended."}]})]))
    E.append(CF(F, "Fighter Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/champion"], "choose": 1,
        "note": "Gain each subclass feature of your Fighter level or lower."})]))
    E.append(CF(F, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Fighter levels 6, 8, 12, 14 and 16."})]))
    E.append(CF(F, "Extra Attack", 5, extra_attack(2)))
    E.append(CF(F, "Tactical Shift", 5, [(None, "fx", {
        "op": "trigger", "event": {"event": "uses_feature.fighter-second-wind"}, "optional": True,
        "condition": {"pred": "used_bonus_action"},
        "then": [{"op": "move", "mode": "move", "distance_feet": HALF_SPEED, "provokes_opportunity_attacks": False}]})]))
    E.append(CF(F, "Indomitable", 9, [
        (None, "fx", {"op": "trigger", "event": {"event": "fails_saving_throw"}, "optional": True,
                      "condition": {"pred": "target_is_source"},
                      "then": [{"op": "spend", "resource": "indomitable", "amount": 1},
                               {"op": "reroll", "rolls": ["saving_throw"], "keep": "new"},
                               {"op": "modifier", "stat": "saving_throw", "mode": "add",
                                "value": {"var": "class_level.fighter"}, "note": "The new roll."}]}),
        (None, "fx", {"op": "resource", "resource": "indomitable", "name": "Indomitable",
                      "max": {"scale": {"by": "class_level.fighter", "steps": [
                          {"from": 9, "value": 1}, {"from": 13, "value": 2}, {"from": 17, "value": 3}]}},
                      "recovery": [{"on": LONG, "amount": "all"}]}),
        ("You can use this feature twice", "sys", ["/effects/1"])]))
    E.append(CF(F, "Tactical Master", 9, [(None, "fx", {
        "op": "trigger", "event": {"event": "attack_roll_made"}, "optional": True,
        "condition": {"pred": "attack_with_mastered_weapon"},
        "then": [{"op": "choice", "id": "replacement_mastery", "choose": 1, "options": [
            {"id": "push", "label": "Push", "effects": [{"op": "grant", "refs": ["dnd5e/weapon-mastery/push"]}]},
            {"id": "sap", "label": "Sap", "effects": [{"op": "grant", "refs": ["dnd5e/weapon-mastery/sap"]}]},
            {"id": "slow", "label": "Slow", "effects": [{"op": "grant", "refs": ["dnd5e/weapon-mastery/slow"]}]}]}],
        "note": "Replaces the weapon's mastery property for that attack."})]))
    E.append(CF(F, "Two Extra Attacks", 11, extra_attack(3)))
    E.append(CF(F, "Studied Attacks", 13, [(None, "fx", {
        "op": "trigger", "event": {"event": "misses_with_attack_roll"},
        "then": [{"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"],
                  "note": "Next attack roll against that creature.",
                  "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self", "which": "next"}}}]})]))
    E.append(CF(F, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-combat-prowess"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Combat Prowess is recommended."})]))
    E.append(CF(F, "Three Extra Attacks", 20, extra_attack(4)))

    S = "Champion"
    E.append(CF(F, "Improved Critical", 3, [(None, "fx", {
        "op": "modifier", "stat": "critical_hit_min_d20", "mode": "min", "value": 19,
        "when": {"any": [{"pred": "attack_uses_weapon"}, {"pred": "attack_is_unarmed_strike"}]}})], sub=S))
    E.append(CF(F, "Remarkable Athlete", 3, [
        (None, "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["initiative", "ability_check.str"],
                      "note": "Strength (Athletics) checks.",
                      "when": {"any": [{"pred": "roll_is", "args": {"roll": "initiative"}},
                                       {"pred": "check_uses_skill", "args": {"skill": "athletics"}}]}}),
        ("In addition, immediately after you score a Critical Hit", "fx", {
            "op": "trigger", "event": {"event": "scores_critical_hit"}, "optional": True,
            "then": [{"op": "move", "mode": "move", "distance_feet": HALF_SPEED, "provokes_opportunity_attacks": False}]})],
        sub=S))
    E.append(CF(F, "Additional Fighting Style", 7, [(None, "fx", {"op": "grant", "refs": STYLES, "choose": 1})], sub=S))
    E.append(CF(F, "Heroic Warrior", 10, [(None, "fx", {
        "op": "trigger", "event": {"event": "turn_start", "whose": "self"}, "optional": True,
        "condition": {"all": [{"pred": "in_combat"}, {"not": {"pred": "has_heroic_inspiration"}}]},
        "then": [{"op": "grant", "refs": ["dnd5e/rule/heroic-inspiration"]}]})], sub=S))
    E.append(CF(F, "Superior Critical", 15, [(None, "fx", {
        "op": "modifier", "stat": "critical_hit_min_d20", "mode": "min", "value": 18,
        "when": {"any": [{"pred": "attack_uses_weapon"}, {"pred": "attack_is_unarmed_strike"}]}})], sub=S))
    E.append(CF(F, "Survivor", 18, [
        (None, "desc", None),
        ("***Defy Death.***", "fx", [
            {"op": "roll_mode", "mode": "advantage", "rolls": ["death_saving_throw"]},
            {"op": "modifier", "stat": "death_save_natural_20_min", "mode": "min", "value": 18,
             "note": "A roll of 18–20 counts as rolling a 20."}]),
        ("***Heroic Rally.***", "fx", {
            "op": "trigger", "event": {"event": "turn_start", "whose": "self"},
            "condition": {"all": [{"pred": "bloodied"}, {"not": {"pred": "at_zero_hp"}}]},
            "then": [{"op": "heal", "amount": {"op": "add", "args": [5, {"var": "ability_mod.con"}]},
                      "target": {"kind": "self"}}]})], sub=S))
    return E


REGISTRY = {
    "stats": [
        {"id": "actions_this_turn", "description": "Number of actions the creature can take this turn.", "pages": [48]},
        {"id": "critical_hit_min_d20", "description": "Lowest d20 roll that scores a Critical Hit (default 20).", "pages": [49]},
        {"id": "death_save_natural_20_min", "description": "Lowest Death Saving Throw roll that counts as a 20.", "pages": [49]}],
    "rolls": [{"id": "death_saving_throw", "description": "A Death Saving Throw.", "pages": [49]}],
    "events": [
        {"id": "fails_ability_check", "description": "The creature fails an ability check.", "pages": [48]},
        {"id": "misses_with_attack_roll", "description": "The creature makes an attack roll against a creature and misses.", "pages": [48]},
        {"id": "scores_critical_hit", "description": "The creature scores a Critical Hit.", "pages": [49]}],
    "predicates": [
        {"id": "resource_available", "description": "The creature has at least one unexpended use of this resource (param).", "params": ["resource"], "type": "predicate", "pages": [48]},
        {"id": "used_bonus_action", "description": "The triggering feature was activated with a Bonus Action.", "type": "predicate", "pages": [48]},
        {"id": "attack_with_mastered_weapon", "description": "The attack uses a weapon whose mastery property the creature can use.", "type": "predicate", "pages": [48]},
        {"id": "attack_is_unarmed_strike", "description": "The attack is an Unarmed Strike.", "type": "predicate", "pages": [49]},
        {"id": "in_combat", "description": "The creature is in combat.", "type": "predicate", "pages": [49]},
        {"id": "has_heroic_inspiration", "description": "The creature has Heroic Inspiration.", "type": "predicate", "pages": [49]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
