#!/usr/bin/env python3
"""L14 (part) — Rogue and Thief features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, col  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
R = "Rogue"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
A = lambda s: f"dnd5e/action/{s}"  # noqa: E731
DC = {"op": "add", "args": [8, {"var": "ability_mod.dex"}, {"var": "proficiency_bonus"}]}
INHERIT = {"kind": "inherit"}


def strike(sid, label, cost, effects, **kw):
    return {"id": sid, "label": f"{label} (Cost: {cost}d6)", "effects": [
        {"op": "modifier", "stat": "sneak_attack_dice", "mode": "add", "value": -cost,
         "note": "Forgo these Sneak Attack dice before rolling."}] + effects, **kw}


def entries():
    E = []
    E.append(CF(R, "Expertise", 1, [
        (None, "fx", {"op": "proficiency", "category": "skill", "expertise": True, "choose": 2,
                      "from": ["proficient_skills"],
                      "note": "Sleight of Hand and Stealth are recommended if proficient."}),
        ("At Rogue level 6", "rule", {"id": "expertise_level_6", "level": 6, "choose": 2})]))
    E.append(CF(R, "Sneak Attack", 1, [
        (None, "fx", {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                      "frequency": {"count": 1, "per": "turn"},
                      "condition": {"all": [
                          {"any": [{"pred": "attack_with_weapon_property", "args": {"property": "finesse"}},
                                   {"pred": "attack_with_ranged_weapon"}]},
                          {"any": [{"pred": "has_advantage_on_roll"},
                                   {"all": [{"pred": "ally_within_feet_of_target", "args": {"feet": 5}},
                                            {"not": {"pred": "has_disadvantage_on_roll"}}]}]}]},
                      "then": [{"op": "damage", "amount": col(R, "Sneak Attack"), "target": INHERIT,
                                "damage_type": {"var": "chosen.weapon_damage_type"}}]}),
        ("You don’t need Advantage on the attack roll", "rule", {
            "id": "ally_alternative", "ally_within_feet_of_target": 5, "ally_not_incapacitated": True,
            "no_disadvantage": True}),
        ("The extra damage increases", "sys", ["/effects/0/then/0"])]))
    E.append(CF(R, "Thieves’ Cant", 1, [(None, "fx", [
        {"op": "proficiency", "category": "language", "items": ["thieves_cant"]},
        {"op": "proficiency", "category": "language", "choose": 1, "from": ["standard_and_rare_language_tables"]}])]))
    E.append(CF(R, "Weapon Mastery", 1, [
        (None, "fx", {"op": "modifier", "stat": "weapon_mastery_kinds", "mode": "set", "value": 2,
                      "note": "Kinds of weapons you are proficient with."}),
        ("Whenever you finish a Long Rest", "rule", {"id": "choices", "weapons": "proficient", "swap_on_long_rest": "all"})]))
    E.append(CF(R, "Cunning Action", 2, [(None, "fx", {
        "op": "activation", "name": "Cunning Action", "cost": "bonus_action", "requires": {"pred": "own_turn"},
        "then": [{"op": "choice", "id": "cunning_action", "choose": 1, "options": [
            {"id": a, "label": a.title(), "effects": [{"op": "reference", "rule": A(a)}]}
            for a in ("dash", "disengage", "hide")]}]})]))
    E.append(CF(R, "Rogue Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/thief"], "choose": 1,
        "note": "Gain each subclass feature of your Rogue level or lower."})]))
    E.append(CF(R, "Steady Aim", 3, [(None, "fx", {
        "op": "activation", "name": "Steady Aim", "cost": "bonus_action",
        "requires": {"not": {"pred": "moved_this_turn"}},
        "then": [{"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "note": "Next attack roll this turn.",
                  "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self"}}},
                 {"op": "speed", "movement": "walk", "mode": "set", "value": 0,
                  "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self"}},
                  "note": "Your Speed is 0."}]})]))
    E.append(CF(R, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Rogue levels 8, 10, 12 and 16."})]))
    poison = strike("poison", "Poison", 1, [
        {"op": "save", "ability": "con", "dc": DC, "target": INHERIT,
         "on_fail": [{"op": "apply_condition", "condition": C("poisoned"), "duration": {"kind": "minutes", "amount": 1}}],
         "repeat": {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}}])
    E.append(CF(R, "Cunning Strike", 5, [
        (None, "fx", {"op": "trigger", "event": {"event": "deals_sneak_attack_damage"}, "optional": True,
                      "then": [{"op": "choice", "id": "cunning_strike", "choose": 1, "options": [
                          poison,
                          strike("trip", "Trip", 1, [{"op": "save", "ability": "dex", "dc": DC,
                                                      "target": {"kind": "inherit", "filter": {"sizes": ["tiny", "small", "medium", "large"]}},
                                                      "on_fail": [{"op": "apply_condition", "condition": C("prone")}]}]),
                          strike("withdraw", "Withdraw", 1, [{"op": "move", "mode": "move", "provokes_opportunity_attacks": False,
                                                              "distance_feet": {"op": "div", "args": [{"var": "speed.walk"}, 2]}}])]}]}),
        (None, "rule", {"id": "timing", "dice_removed_before_rolling": True, "effect_after_damage": True}),
        ("If a Cunning Strike effect requires a saving throw", "rule", {"id": "save_dc", "dc": DC}),
        ("***Poison (Cost: 1d6).***", "sys", ["/effects/0/then/0/options/0"]),
        ("To use this effect, you must have a Poisoner’s Kit", "rule", {
            "id": "poison_requires", "option": "poison", "requires_on_person": "dnd5e/tool/poisoners-kit"}),
        ("***Trip (Cost: 1d6).***", "sys", ["/effects/0/then/0/options/1"]),
        ("***Withdraw (Cost: 1d6).***", "sys", ["/effects/0/then/0/options/2"])]))
    E.append(CF(R, "Uncanny Dodge", 5, [(None, "fx", {
        "op": "trigger", "event": {"event": "hit_by_attack_roll"}, "cost": "reaction", "optional": True,
        "condition": {"pred": "can_see", "args": {"who": "attacker"}},
        "then": [{"op": "modifier", "stat": "damage_taken", "mode": "multiply", "value": 0.5,
                  "note": "Halve the attack's damage against you (round down)."}]})]))
    E.append(CF(R, "Evasion", 7, [(None, "fx", {
        "op": "modifier", "stat": "evasion", "mode": "set", "value": 1,
        "when": {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}},
        "note": "Dexterity saves for half damage: no damage on a success, half on a failure."})]))
    E.append(CF(R, "Reliable Talent", 7, [(None, "fx", {
        "op": "modifier", "stat": "d20_roll", "mode": "min", "value": 10,
        "when": {"pred": "check_uses_own_proficiency"}, "note": "Ability checks using a skill or tool proficiency."})]))
    E.append(CF(R, "Improved Cunning Strike", 11, [(None, "rule", {
        "id": "two_effects", "feature": "dnd5e/feature/rogue-cunning-strike", "max_effects": 2, "pay_each_cost": True})]))
    E.append(CF(R, "Devious Strikes", 14, [
        (None, "rule", {"id": "new_options", "adds_options_to": "dnd5e/feature/rogue-cunning-strike"}),
        (None, "fx", {"op": "choice", "id": "devious_strikes", "choose": 1, "options": [
            strike("daze", "Daze", 2, [{"op": "save", "ability": "con", "dc": DC, "target": INHERIT,
                                       "on_fail": [{"op": "restrict", "restrictions": ["more_than_one_of_move_action_bonus_action"],
                                                    "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "target", "which": "next"}}}]}]),
            strike("knock_out", "Knock Out", 6, [{"op": "save", "ability": "con", "dc": DC, "target": INHERIT,
                                                 "on_fail": [{"op": "apply_condition", "condition": C("unconscious"),
                                                              "duration": {"kind": "minutes", "amount": 1},
                                                              "note": "Ends early if the target takes any damage."}],
                                                 "repeat": {"on": {"event": "turn_end", "whose": "target", "which": "each"},
                                                            "ends": "effect_on_self"}}]),
            strike("obscure", "Obscure", 3, [{"op": "save", "ability": "dex", "dc": DC, "target": INHERIT,
                                             "on_fail": [{"op": "apply_condition", "condition": C("blinded"),
                                                          "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "target", "which": "next"}}}]}])]}),
        ("***Daze (Cost: 2d6).***", "sys", ["/effects/0/options/0"]),
        ("***Knock Out (Cost: 6d6).***", "sys", ["/effects/0/options/1"]),
        ("***Obscure (Cost: 3d6).***", "sys", ["/effects/0/options/2"])]))
    E.append(CF(R, "Slippery Mind", 15, [(None, "fx", {"op": "proficiency", "category": "saving_throw",
                                                         "items": ["wis", "cha"]})]))
    E.append(CF(R, "Elusive", 18, [(None, "fx", {
        "op": "restrict", "restrictions": ["attack_rolls_against_have_advantage"],
        "when": {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}}})]))
    E.append(CF(R, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-the-night-spirit"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of the Night Spirit is recommended."})]))
    E.append(CF(R, "Stroke of Luck", 20, [
        (None, "fx", {"op": "trigger", "event": {"event": "fails_d20_test"}, "optional": True,
                      "frequency": {"count": 1, "per": "short_rest"},
                      "then": [{"op": "modifier", "stat": "d20_roll", "mode": "set", "value": 20}]}),
        ("Once you use this feature", "rule", {"id": "recharge", "on": ["short_rest_finished", "long_rest_finished"]})]))

    S = "Thief"
    E.append(CF(R, "Fast Hands", 3, [
        (None, "fx", {"op": "activation", "name": "Fast Hands", "cost": "bonus_action",
                      "then": [{"op": "choice", "id": "fast_hands", "choose": 1, "options": [
                          {"id": "sleight_of_hand", "label": "Sleight of Hand", "effects": [
                              {"op": "check", "ability": "dex", "skill": "sleight_of_hand",
                               "note": "Pick a lock or disarm a trap with Thieves' Tools, or pick a pocket."}]},
                          {"id": "use_an_object", "label": "Use an Object", "effects": [
                              {"op": "reference", "rule": A("utilize")},
                              {"op": "reference", "rule": A("magic"),
                               "note": "Only to use a magic item that requires that action."}]}]}]}),
        ("***Sleight of Hand.***", "sys", ["/effects/0/then/0/options/0"]),
        ("***Sleight of Hand.***", "ref", ["dnd5e/tool/thieves-tools"]),
        ("***Use an Object.***", "sys", ["/effects/0/then/0/options/1"])], sub=S))
    E.append(CF(R, "Second-Story Work", 3, [
        (None, "desc", None),
        ("***Climber.***", "fx", {"op": "speed", "movement": "climb", "mode": "equal_to_walk", "value": 0}),
        ("***Jumper.***", "fx", {"op": "modifier", "stat": "jump_ability", "mode": "set", "value": {"var": "ability_score.dex"},
                                "note": "Dexterity rather than Strength determines your jump distance."})], sub=S))
    E.append(CF(R, "Supreme Sneak", 9, [
        (None, "rule", {"id": "new_option", "adds_options_to": "dnd5e/feature/rogue-cunning-strike"}),
        ("***Stealth Attack (Cost: 1d6).***", "fx", {
            "op": "modifier", "stat": "sneak_attack_dice", "mode": "add", "value": -1,
            "when": {"pred": "has_condition_from", "args": {"condition": "invisible", "source": "hide"}},
            "note": "The attack doesn't end the Hide action's Invisible condition if you end the turn behind Three-Quarters or Total Cover."})], sub=S))
    E.append(CF(R, "Use Magic Device", 13, [
        (None, "desc", None),
        ("***Attunement.***", "fx", {"op": "modifier", "stat": "max_attuned_items", "mode": "max", "value": 4}),
        ("***Charges.***", "rule", {"id": "charges", "on": "expends_item_charges", "roll": "1d6",
                                   "on_6": "no_charges_expended"}),
        ("***Scrolls.***", "rule", {"id": "scrolls", "item": "dnd5e/magic-item/spell-scroll", "ability": "int",
                                   "reliable_levels": [0, 1],
                                   "higher_level_check": {"ability": "int", "skill": "arcana",
                                                          "dc": {"op": "add", "args": [10, {"var": "spell_level"}]},
                                                          "on_fail": "scroll_disintegrates"}})], sub=S))
    E.append(CF(R, "Thief’s Reflexes", 17, [(None, "rule", {
        "id": "two_turns", "round": "first_of_combat", "turns": [{"initiative": "normal"},
                                                                 {"initiative": "normal_minus_10"}]})], sub=S))
    return E


REGISTRY = {
    "stats": [
        {"id": "sneak_attack_dice", "description": "Number of Sneak Attack damage dice rolled.", "pages": [63]},
        {"id": "d20_roll", "description": "The number rolled on the d20.", "pages": [63]},
        {"id": "jump_ability", "description": "Ability score used to determine jump distance.", "pages": [64]},
        {"id": "max_attuned_items", "description": "Maximum magic items the creature can be attuned to at once.", "pages": [64]}],
    "restrictions": [{"id": "attack_rolls_against_have_advantage", "description": "No attack roll can have Advantage against the creature.", "pages": [63]}],
    "events": [
        {"id": "deals_sneak_attack_damage", "description": "The creature deals Sneak Attack damage.", "pages": [63]}],
    "predicates": [
        {"id": "attack_with_weapon_property", "description": "The attack uses a weapon with this property (param).", "params": ["property"], "type": "predicate", "pages": [61]},
        {"id": "attack_with_ranged_weapon", "description": "The attack uses a Ranged weapon.", "type": "predicate", "pages": [61]},
        {"id": "has_advantage_on_roll", "description": "The creature has Advantage on the roll.", "type": "predicate", "pages": [61]},
        {"id": "has_disadvantage_on_roll", "description": "The creature has Disadvantage on the roll.", "type": "predicate", "pages": [61]},
        {"id": "ally_within_feet_of_target", "description": "An ally without the Incapacitated condition is within N feet (param) of the target.", "params": ["feet"], "type": "predicate", "pages": [61]},
        {"id": "moved_this_turn", "description": "The creature has moved during this turn.", "type": "predicate", "pages": [62]},
        {"id": "check_uses_own_proficiency", "description": "The ability check uses one of the creature's skill or tool proficiencies.", "type": "predicate", "pages": [63]},
        {"id": "has_condition_from", "description": "The creature has the condition (param) from the given source (param).", "params": ["condition", "source"], "type": "predicate", "pages": [64]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
