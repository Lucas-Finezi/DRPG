#!/usr/bin/env python3
"""L14 (part) — Ranger and Hunter features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, col, spellcasting  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
R = "Ranger"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
WIS = {"var": "ability_mod.wis"}
WIS1 = {"op": "max", "args": [1, WIS]}
HM = "dnd5e/spell/hunters-mark"
MARKED = {"pred": "marked_by_spell", "args": {"spell": "hunters-mark"}}
STYLES = ["dnd5e/feat/archery", "dnd5e/feat/defense", "dnd5e/feat/great-weapon-fighting",
          "dnd5e/feat/two-weapon-fighting"]
SWAP = {"id": "swap", "on": ["short_rest_finished", "long_rest_finished"], "replace_with": "other_option"}


def entries():
    E = []
    E.append(CF(R, "Spellcasting", 1, spellcasting(
        R, "wis", ["dnd5e/gear/druidic-focus"], 2, ["Cure Wounds", "Ensnaring Strike"], "long_rest_one")))
    E.append(CF(R, "Favored Enemy", 1, [
        (None, "fx", [{"op": "grant", "refs": [HM], "note": "Always prepared."},
                      {"op": "resource", "resource": "favored_enemy", "name": "Favored Enemy",
                       "max": col(R, "Favored Enemy"), "recovery": [{"on": LONG, "amount": "all"}]},
                      {"op": "activation", "cost": "none", "uses": {"resource": "favored_enemy", "amount": 1},
                       "then": [{"op": "cast_spell", "spell": HM, "slot": "none"}],
                       "note": "Casting time as normal for the spell."}]),
        ("The number of times you can cast the spell", "sys", ["/effects/1"])]))
    E.append(CF(R, "Weapon Mastery", 1, [
        (None, "fx", {"op": "modifier", "stat": "weapon_mastery_kinds", "mode": "set", "value": 2,
                      "note": "Kinds of weapons you are proficient with."}),
        ("Whenever you finish a Long Rest", "rule", {"id": "choices", "weapons": "proficient", "swap_on_long_rest": "all"})]))
    E.append(CF(R, "Deft Explorer", 2, [
        (None, "desc", None),
        ("***Expertise.***", "fx", {"op": "proficiency", "category": "skill", "expertise": True, "choose": 1,
                                   "from": ["proficient_skills_without_expertise"]}),
        ("***Languages.***", "fx", {"op": "proficiency", "category": "language", "choose": 2,
                                   "from": ["standard_and_rare_language_tables"]})]))
    E.append(CF(R, "Fighting Style", 2, [
        (None, "fx", {"op": "choice", "id": "fighting_style", "choose": 1, "options": [
            {"id": "feat", "label": "Fighting Style feat", "effects": [{"op": "grant", "refs": STYLES, "choose": 1}]},
            {"id": "druidic_warrior", "label": "Druidic Warrior", "effects": [
                {"op": "grant", "refs": ["dnd5e/spell-list/druid"], "choose": 2,
                 "note": "Two Druid cantrips; Guidance and Starry Wisp are recommended."}]}]}),
        ("***Druidic Warrior.***", "rule", {"id": "druidic_warrior", "cantrips": 2, "from": "dnd5e/spell-list/druid",
                                           "recommended": ["dnd5e/spell/guidance", "dnd5e/spell/starry-wisp"],
                                           "count_as": "dnd5e/class/ranger", "ability": "wis",
                                           "replace": {"on": "level_gained", "count": 1}})]))
    E.append(CF(R, "Ranger Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/hunter"], "choose": 1,
        "note": "Gain each subclass feature of your Ranger level or lower."})]))
    E.append(CF(R, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Ranger levels 8, 12 and 16."})]))
    E.append(CF(R, "Extra Attack", 5, [(None, "fx", {"op": "modifier", "stat": "attacks_per_attack_action",
                                                       "mode": "max", "value": 2})]))
    E.append(CF(R, "Roving", 6, [(None, "fx", [
        {"op": "speed", "movement": "walk", "mode": "add", "value": 10,
         "when": {"not": {"pred": "wearing_armor", "args": {"category": "heavy"}}}},
        {"op": "speed", "movement": "climb", "mode": "equal_to_walk", "value": 0},
        {"op": "speed", "movement": "swim", "mode": "equal_to_walk", "value": 0}])]))
    E.append(CF(R, "Expertise", 9, [(None, "fx", {
        "op": "proficiency", "category": "skill", "expertise": True, "choose": 2,
        "from": ["proficient_skills_without_expertise"]})]))
    E.append(CF(R, "Tireless", 10, [
        (None, "desc", None),
        ("***Temporary Hit Points.***", "fx", [
            {"op": "activation", "name": "Tireless", "cost": "action", "action": "dnd5e/action/magic",
             "uses": {"resource": "tireless", "amount": 1},
             "then": [{"op": "temp_hp", "target": {"kind": "self"},
                       "amount": {"op": "max", "args": [1, {"op": "add", "args": ["1d8", WIS]}]}}]},
            {"op": "resource", "resource": "tireless", "max": WIS1, "recovery": [{"on": LONG, "amount": "all"}]}]),
        ("***Decrease Exhaustion.***", "fx", {"op": "trigger", "event": SHORT,
                                             "then": [{"op": "remove_condition", "conditions": [C("exhaustion")],
                                                       "levels": 1}]})]))
    E.append(CF(R, "Relentless Hunter", 13, [(None, "rule", {
        "id": "concentration", "spell": HM, "damage_breaks_concentration": False})]))
    E.append(CF(R, "Nature’s Veil", 14, [
        (None, "fx", {"op": "activation", "name": "Nature’s Veil", "cost": "bonus_action",
                      "uses": {"resource": "natures_veil", "amount": 1},
                      "then": [{"op": "apply_condition", "condition": C("invisible"), "target": {"kind": "self"},
                                "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self",
                                                                              "which": "next"}}}]}),
        ("You can use this feature a number of times", "fx", {
            "op": "resource", "resource": "natures_veil", "max": WIS1, "recovery": [{"on": LONG, "amount": "all"}]})]))
    E.append(CF(R, "Precise Hunter", 17, [(None, "fx", {
        "op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "when": MARKED})]))
    E.append(CF(R, "Feral Senses", 18, [(None, "fx", {"op": "sense", "sense": "blindsight", "range_feet": 30})]))
    E.append(CF(R, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-dimensional-travel"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Dimensional Travel is recommended."})]))
    E.append(CF(R, "Foe Slayer", 20, [(None, "rule", {"id": "damage_die", "spell": HM, "die": "d10",
                                                         "replaces": "d6"})]))

    S = "Hunter"
    E.append(CF(R, "Hunter’s Lore", 3, [(None, "rule", {
        "id": "know_defenses", "while": "target_marked_by_hunters_mark",
        "reveals": ["immunities", "resistances", "vulnerabilities"]})], sub=S))
    E.append(CF(R, "Hunter’s Prey", 3, [
        (None, "fx", {"op": "choice", "id": "hunters_prey", "choose": 1, "options": [
            {"id": "colossus_slayer", "label": "Colossus Slayer", "effects": [
                {"op": "trigger", "event": {"event": "hits_with_attack_roll"},
                 "condition": {"all": [{"pred": "attack_uses_weapon"}, {"pred": "target_missing_hit_points"}]},
                 "frequency": {"count": 1, "per": "turn"},
                 "then": [{"op": "damage", "amount": "1d8", "damage_type": {"var": "chosen.weapon_damage_type"},
                           "target": {"kind": "inherit"}}]}]},
            {"id": "horde_breaker", "label": "Horde Breaker", "effects": [
                {"op": "trigger", "event": {"event": "attack_roll_made"}, "optional": True,
                 "condition": {"all": [{"pred": "own_turn"}, {"pred": "attack_uses_weapon"}]},
                 "frequency": {"count": 1, "per": "turn"},
                 "then": [{"op": "attack", "attack_type": "melee",
                           "note": "Same weapon; a different creature within 5 feet of the original target, within the weapon's range, not attacked this turn."}]}]}]}),
        (None, "rule", SWAP),
        ("***Colossus Slayer.***", "sys", ["/effects/0/options/0"]),
        ("***Horde Breaker.***", "sys", ["/effects/0/options/1"])], sub=S))
    E.append(CF(R, "Defensive Tactics", 7, [
        (None, "fx", {"op": "choice", "id": "defensive_tactics", "choose": 1, "options": [
            {"id": "escape_the_horde", "label": "Escape the Horde", "effects": [
                {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "direction": "against",
                 "when": {"pred": "attack_is_opportunity_attack"}}]},
            {"id": "multiattack_defense", "label": "Multiattack Defense", "effects": [
                {"op": "trigger", "event": {"event": "hit_by_attack_roll"},
                 "then": [{"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "direction": "against",
                           "when": {"pred": "attacker_is_trigger_creature"},
                           "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "any"}},
                           "note": "All other attack rolls by that creature against you this turn."}]}]}]}),
        (None, "rule", SWAP),
        ("***Escape the Horde.***", "sys", ["/effects/0/options/0"]),
        ("***Multiattack Defense.***", "sys", ["/effects/0/options/1"])], sub=S))
    E.append(CF(R, "Superior Hunter’s Prey", 11, [(None, "fx", {
        "op": "trigger", "event": {"event": "deals_damage"}, "optional": True, "condition": MARKED,
        "frequency": {"count": 1, "per": "turn"},
        "then": [{"op": "reference", "rule": HM,
                  "target": {"kind": "creature", "must_see": True},
                  "note": "Deal the spell's extra damage to a different creature within 30 feet of the first."}]})], sub=S))
    E.append(CF(R, "Superior Hunter’s Defense", 15, [(None, "fx", {
        "op": "trigger", "event": {"event": "damage_taken"}, "cost": "reaction", "optional": True,
        "then": [{"op": "defense", "kind": "resistance", "damage_types": [{"var": "chosen.trigger_damage_type"}],
                  "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "any"}},
                  "note": "That damage and any other damage of the same type."}]})], sub=S))
    return E


REGISTRY = {
    "events": [{"id": "deals_damage", "description": "The creature deals damage to a creature.", "pages": [61]}],
    "predicates": [
        {"id": "marked_by_spell", "description": "The target is currently marked by the source's spell (param: spell slug).", "params": ["spell"], "type": "predicate", "pages": [59]},
        {"id": "target_missing_hit_points", "description": "The target is missing any of its Hit Points.", "type": "predicate", "pages": [61]},
        {"id": "attack_is_opportunity_attack", "description": "The attack is an Opportunity Attack.", "type": "predicate", "pages": [61]},
        {"id": "attacker_is_trigger_creature", "description": "The attacker is the creature that caused the trigger.", "type": "predicate", "pages": [61]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
