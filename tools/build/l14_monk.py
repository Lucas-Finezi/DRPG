#!/usr/bin/env python3
"""L14 (part) — Monk and Warrior of the Open Hand features."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from classlib import CF, active, col  # noqa: E402
from entrylib import extend_registries, write_entry  # noqa: E402

LOT = "L14"
M = "Monk"
LONG = {"event": "long_rest_finished"}
SHORT = {"event": "short_rest_finished"}
C = lambda s: f"dnd5e/condition/{s}"  # noqa: E731
A = lambda s: f"dnd5e/action/{s}"  # noqa: E731
MA_DIE = col(M, "Martial Arts")
FP = lambda n: {"resource": "focus_points", "amount": n}  # noqa: E731
UNARMORED = {"all": [{"not": {"pred": "wearing_armor_any"}}, {"not": {"pred": "using_shield"}}]}
MONK_DC = {"op": "add", "args": [8, {"var": "ability_mod.wis"}, {"var": "proficiency_bonus"}]}
DEX = {"var": "ability_mod.dex"}
NEXT_TURN_START = {"kind": "until_event", "until": {"event": "turn_start", "whose": "source"}}
MONK_HIT = {"any": [{"pred": "attack_with_monk_weapon"}, {"pred": "attack_is_unarmed_strike"}]}


def entries():
    E = []
    E.append(CF(M, "Martial Arts", 1, [
        (None, "rule", {"id": "monk_weapons", "weapons": ["simple_melee", "martial_melee_with_light_property"],
                        "light_property": "dnd5e/weapon-property/light"}),
        ("You gain the following benefits", "rule", {"id": "requirements", "requires": [
            "unarmed_or_only_monk_weapons", "no_armor", "no_shield"]}),
        ("***Bonus Unarmed Strike.***", "fx", {
            "op": "activation", "name": "Bonus Unarmed Strike", "cost": "bonus_action",
            "requires": {"all": [UNARMORED, {"pred": "only_monk_weapons_or_unarmed"}]},
            "then": [{"op": "reference", "rule": "dnd5e/rule/unarmed-strike"}]}),
        ("***Martial Arts Die.***", "fx", {
            "op": "modifier", "stat": "weapon_damage_die", "mode": "max", "value": MA_DIE,
            "when": {"all": [UNARMORED, {"pred": "only_monk_weapons_or_unarmed"}, MONK_HIT]},
            "note": "Roll the Martial Arts die in place of the normal damage."}),
        ("***Dexterous Attacks.***", "fx", [
            {"op": "modifier", "stat": "attack_ability", "mode": "set", "value": DEX, "id": "dex_attacks",
             "when": {"all": [UNARMORED, {"pred": "only_monk_weapons_or_unarmed"}, MONK_HIT]},
             "note": "Optional: Dexterity instead of Strength for attack and damage rolls."},
            {"op": "modifier", "stat": "unarmed_strike_save_dc_ability", "mode": "set", "value": DEX,
             "when": UNARMORED, "note": "Optional, for the Grapple or Shove option of Unarmed Strike."}])]))
    E.append(CF(M, "Unarmored Defense", 1, [(None, "fx", {
        "op": "modifier", "stat": "base_ac", "mode": "set",
        "value": {"op": "add", "args": [10, DEX, {"var": "ability_mod.wis"}]}, "when": UNARMORED})]))
    E.append(CF(M, "Monk’s Focus", 2, [
        (None, "fx", {"op": "resource", "resource": "focus_points", "name": "Focus Points", "max": col(M, "Focus Points"),
                      "recovery": [{"on": SHORT, "amount": "all"}, {"on": LONG, "amount": "all"}]}),
        ("You can expend these points", "rule", {"id": "known", "features": ["flurry_of_blows", "patient_defense",
                                                                             "step_of_the_wind"]}),
        ("When you expend a Focus Point", "sys", ["/effects/0"]),
        ("Some features that use Focus Points", "rule", {"id": "focus_save_dc", "dc": MONK_DC}),
        ("***Flurry of Blows.***", "fx", {
            "op": "activation", "name": "Flurry of Blows", "cost": "bonus_action", "uses": FP(1),
            "then": [{"op": "repeat", "times": 2, "then": [{"op": "reference", "rule": "dnd5e/rule/unarmed-strike"}]}]}),
        ("***Patient Defense.***", "fx", {
            "op": "choice", "id": "patient_defense", "choose": 1, "options": [
                {"id": "free", "label": "Disengage", "effects": [{"op": "activation", "cost": "bonus_action",
                                                                  "then": [{"op": "reference", "rule": A("disengage")}]}]},
                {"id": "focus", "label": "Disengage and Dodge (1 Focus Point)", "effects": [
                    {"op": "activation", "cost": "bonus_action", "uses": FP(1),
                     "then": [{"op": "reference", "rule": A("disengage")}, {"op": "reference", "rule": A("dodge")}]}]}]}),
        ("***Step of the Wind.***", "fx", {
            "op": "choice", "id": "step_of_the_wind", "choose": 1, "options": [
                {"id": "free", "label": "Dash", "effects": [{"op": "activation", "cost": "bonus_action",
                                                             "then": [{"op": "reference", "rule": A("dash")}]}]},
                {"id": "focus", "label": "Disengage and Dash (1 Focus Point)", "effects": [
                    {"op": "activation", "cost": "bonus_action", "uses": FP(1),
                     "then": [{"op": "reference", "rule": A("disengage")}, {"op": "reference", "rule": A("dash")},
                              {"op": "modifier", "stat": "jump_distance", "mode": "multiply", "value": 2,
                               "duration": {"kind": "until_event", "until": {"event": "turn_end", "whose": "self"}}}]}]}]})]))
    E.append(CF(M, "Unarmored Movement", 2, [(None, "fx", {
        "op": "speed", "movement": "walk", "mode": "add", "when": UNARMORED,
        "value": {"scale": {"by": "class_level.monk", "steps": [
            {"from": 2, "value": 10}, {"from": 6, "value": 15}, {"from": 10, "value": 20}, {"from": 14, "value": 25},
            {"from": 18, "value": 30}]}}, "note": "Unarmored Movement column of the Monk Features table."})]))
    E.append(CF(M, "Uncanny Metabolism", 2, [
        (None, "fx", {"op": "trigger", "event": {"event": "initiative_rolled"}, "optional": True,
                      "frequency": {"count": 1, "per": "long_rest"},
                      "then": [{"op": "restore", "resource": "focus_points", "amount": "all"},
                               {"op": "heal", "amount": {"op": "add", "args": [{"var": "class_level.monk"}, MA_DIE]},
                                "target": {"kind": "self"}}]})]))
    E.append(CF(M, "Deflect Attacks", 3, [
        (None, "fx", {"op": "trigger", "event": {"event": "hit_by_attack_roll"}, "cost": "reaction", "optional": True,
                      "condition": {"any": [{"pred": "deals_damage_type", "args": {"type": t}}
                                            for t in ("bludgeoning", "piercing", "slashing")]},
                      "then": [{"op": "modifier", "stat": "damage_taken", "mode": "add",
                                "value": {"op": "neg", "args": [{"op": "add", "args": [
                                    "1d10", DEX, {"var": "class_level.monk"}]}]}}]}),
        ("If you reduce the damage to 0", "fx", {
            "op": "activation", "cost": "none", "uses": FP(1),
            "requires": {"pred": "damage_reduced_to_zero"},
            "then": [{"op": "save", "ability": "dex", "dc": MONK_DC,
                      "target": {"kind": "creature", "must_see": True},
                      "note": "A creature within 5 feet (melee attack) or 60 feet not behind Total Cover (ranged attack).",
                      "on_fail": [{"op": "damage", "damage_type": {"var": "chosen.attack_damage_type"},
                                   "amount": {"op": "add", "args": [MA_DIE, MA_DIE, DEX]}}]}]})]))
    E.append(CF(M, "Monk Subclass", 3, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/subclass/warrior-of-the-open-hand"], "choose": 1,
        "note": "Gain each subclass feature of your Monk level or lower."})]))
    E.append(CF(M, "Ability Score Improvement", 4, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/ability-score-improvement"],
        "note": "Or another feat you qualify for; again at Monk levels 8, 12 and 16."})]))
    E.append(CF(M, "Slow Fall", 4, [(None, "fx", {
        "op": "trigger", "event": {"event": "falls"}, "cost": "reaction", "optional": True,
        "then": [{"op": "modifier", "stat": "damage_taken", "mode": "add",
                  "value": {"op": "neg", "args": [{"op": "mul", "args": [5, {"var": "class_level.monk"}]}]},
                  "note": "Damage from the fall."}]})]))
    E.append(CF(M, "Extra Attack", 5, [(None, "fx", {"op": "modifier", "stat": "attacks_per_attack_action",
                                                       "mode": "max", "value": 2})]))
    E.append(CF(M, "Stunning Strike", 5, [(None, "fx", {
        "op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True, "condition": MONK_HIT,
        "frequency": {"count": 1, "per": "turn"},
        "then": [{"op": "spend", "resource": "focus_points", "amount": 1},
                 {"op": "save", "ability": "con", "dc": MONK_DC, "target": {"kind": "inherit"},
                  "on_fail": [{"op": "apply_condition", "condition": C("stunned"), "duration": NEXT_TURN_START}],
                  "on_success": [{"op": "speed", "movement": "walk", "mode": "multiply", "value": 0.5,
                                  "duration": NEXT_TURN_START},
                                 {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "direction": "against",
                                  "duration": NEXT_TURN_START, "note": "Only the next attack roll against the target."}]}]})]))
    E.append(CF(M, "Empowered Strikes", 6, [(None, "rule", {
        "id": "damage_type_choice", "attack": "unarmed_strike", "choose_from": ["force", "normal_damage_type"]})]))
    E.append(CF(M, "Evasion", 7, [
        (None, "fx", {"op": "modifier", "stat": "evasion", "mode": "set", "value": 1,
                      "when": {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}},
                      "note": "Dexterity saves for half damage: no damage on a success, half on a failure."}),
        ("You don’t benefit from this feature", "sys", ["/effects/0"])]))
    E.append(CF(M, "Acrobatic Movement", 9, [(None, "rule", {
        "id": "acrobatic_movement", "when": "unarmored_no_shield", "own_turn_only": True,
        "move_along": ["vertical_surfaces", "liquids"], "falls_during_movement": False})]))
    E.append(CF(M, "Heightened Focus", 10, [
        (None, "rule", {"id": "improves", "features": ["flurry_of_blows", "patient_defense", "step_of_the_wind"]}),
        ("***Flurry of Blows.***", "rule", {"id": "flurry_of_blows", "unarmed_strikes": 3}),
        ("***Patient Defense.***", "fx", {"op": "trigger", "event": {"event": "uses_feature.monk-monks-focus.patient_defense"},
                                         "condition": {"pred": "spent_focus_point"},
                                         "then": [{"op": "temp_hp", "amount": {"op": "add", "args": [MA_DIE, MA_DIE]}}]}),
        ("***Step of the Wind.***", "rule", {"id": "step_of_the_wind", "carry_willing_creature": {
            "within_feet": 5, "max_size": "large", "until": "end_of_turn", "provokes_opportunity_attacks": False}})]))
    E.append(CF(M, "Self-Restoration", 10, [
        (None, "fx", {"op": "trigger", "event": {"event": "turn_end", "whose": "self"}, "optional": True,
                      "then": [{"op": "remove_condition", "conditions": [C("charmed"), C("frightened"), C("poisoned")],
                                "count": 1}]}),
        ("In addition, forgoing food and drink", "rule", {"id": "no_starvation_exhaustion", "food_and_drink_exhaustion": False})]))
    E.append(CF(M, "Deflect Energy", 13, [(None, "rule", {
        "id": "any_damage_type", "feature": "dnd5e/feature/monk-deflect-attacks", "damage_types": "any"})]))
    E.append(CF(M, "Disciplined Survivor", 14, [
        (None, "fx", {"op": "proficiency", "category": "saving_throw", "items": ["str", "dex", "con", "int", "wis", "cha"]}),
        ("Additionally, whenever you make a saving throw and fail", "fx", {
            "op": "trigger", "event": {"event": "fails_saving_throw"}, "optional": True,
            "condition": {"pred": "target_is_source"},
            "then": [{"op": "spend", "resource": "focus_points", "amount": 1},
                     {"op": "reroll", "rolls": ["saving_throw"], "keep": "new"}]})]))
    E.append(CF(M, "Perfect Focus", 15, [(None, "fx", {
        "op": "trigger", "event": {"event": "initiative_rolled"},
        "condition": {"not": {"pred": "used_feature_this_trigger", "args": {"feature": "monk-uncanny-metabolism"}}},
        "then": [{"op": "restore", "resource": "focus_points", "amount": {
            "op": "max", "args": [0, {"op": "sub", "args": [4, {"var": "resource.focus_points"}]}]}}]})]))
    E.append(CF(M, "Superior Defense", 18, [(None, "fx", {
        "op": "trigger", "event": {"event": "turn_start", "whose": "self"}, "optional": True,
        "then": [{"op": "spend", "resource": "focus_points", "amount": 3},
                 {"op": "defense", "kind": "resistance",
                  "damage_types": ["acid", "bludgeoning", "cold", "fire", "lightning", "necrotic", "piercing", "poison",
                                   "psychic", "radiant", "slashing", "thunder"],
                  "duration": {"kind": "minutes", "amount": 1}, "note": "All damage except Force; ends early if Incapacitated."}]})]))
    E.append(CF(M, "Epic Boon", 19, [(None, "fx", {
        "op": "grant", "refs": ["dnd5e/feat/boon-of-irresistible-offense"],
        "note": "An Epic Boon feat or another feat you qualify for; Boon of Irresistible Offense is recommended."})]))
    E.append(CF(M, "Body and Mind", 20, [(None, "fx", [
        {"op": "modifier", "stat": "ability_score.dex", "mode": "add", "value": 4},
        {"op": "modifier", "stat": "ability_score.wis", "mode": "add", "value": 4},
        {"op": "modifier", "stat": "ability_score_max.dex", "mode": "max", "value": 25},
        {"op": "modifier", "stat": "ability_score_max.wis", "mode": "max", "value": 25}])]))

    S = "Warrior of the Open Hand"
    E.append(CF(M, "Open Hand Technique", 3, [
        (None, "fx", {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
                      "condition": {"pred": "attack_from_feature", "args": {"feature": "flurry_of_blows"}},
                      "then": [{"op": "choice", "id": "technique", "choose": 1, "options": [
                          {"id": "addle", "label": "Addle", "effects": [
                              {"op": "restrict", "restrictions": ["make_opportunity_attacks"], "target": {"kind": "inherit"},
                               "duration": {"kind": "until_event", "until": {"event": "turn_start", "whose": "target"}}}]},
                          {"id": "push", "label": "Push", "effects": [
                              {"op": "save", "ability": "str", "dc": MONK_DC, "target": {"kind": "inherit"},
                               "on_fail": [{"op": "move", "mode": "push", "distance_feet": 15}]}]},
                          {"id": "topple", "label": "Topple", "effects": [
                              {"op": "save", "ability": "dex", "dc": MONK_DC, "target": {"kind": "inherit"},
                               "on_fail": [{"op": "apply_condition", "condition": C("prone")}]}]}]}]}),
        ("***Addle.***", "sys", ["/effects/0/then/0/options/0"]),
        ("***Push.***", "sys", ["/effects/0/then/0/options/1"]),
        ("***Topple.***", "sys", ["/effects/0/then/0/options/2"])], sub=S))
    E.append(CF(M, "Wholeness of Body", 6, [
        (None, "fx", {"op": "activation", "name": "Wholeness of Body", "cost": "bonus_action",
                      "uses": {"resource": "wholeness_of_body", "amount": 1},
                      "then": [{"op": "heal", "target": {"kind": "self"}, "amount": {"op": "max", "args": [
                          1, {"op": "add", "args": [MA_DIE, {"var": "ability_mod.wis"}]}]}}]}),
        ("You can use this feature a number of times", "fx", {
            "op": "resource", "resource": "wholeness_of_body", "max": {"op": "max", "args": [1, {"var": "ability_mod.wis"}]},
            "recovery": [{"on": LONG, "amount": "all"}]})], sub=S))
    E.append(CF(M, "Fleet Step", 11, [(None, "fx", {
        "op": "trigger", "event": {"event": "bonus_action_taken"}, "optional": True,
        "condition": {"not": {"pred": "attack_from_feature", "args": {"feature": "step_of_the_wind"}}},
        "then": [{"op": "reference", "rule": "dnd5e/feature/monk-monks-focus",
                  "note": "Use Step of the Wind immediately after that Bonus Action."}]})], sub=S))
    E.append(CF(M, "Quivering Palm", 17, [
        (None, "fx", [
            {"op": "trigger", "event": {"event": "hits_with_attack_roll"}, "optional": True,
             "condition": {"pred": "attack_is_unarmed_strike"},
             "then": [{"op": "spend", "resource": "focus_points", "amount": 4},
                      {"op": "reference", "rule": "dnd5e/feature/warrior-of-the-open-hand-quivering-palm", "id": "vibrations",
                       "target": {"kind": "inherit"},
                       "duration": {"kind": "days", "amount": {"var": "class_level.monk"}},
                       "note": "Harmless imperceptible vibrations; one creature at a time."}]},
            {"op": "activation", "name": "End the vibrations", "cost": "action",
             "requires": {"pred": "same_plane_as_target"},
             "then": [{"op": "save", "ability": "con", "dc": MONK_DC, "half_on_success": True,
                       "on_fail": [{"op": "damage", "amount": "10d12", "damage_type": "force"}]}]}]),
        ("Alternatively, when you take the Attack action", "rule", {
            "id": "end_with_attack", "forgo_one_attack_of_attack_action": True, "own_turn": True}),
        ("You can have only one creature", "rule", {"id": "limits", "max_targets": 1, "end_harmlessly_cost": "none"})],
        sub=S))
    return E


REGISTRY = {
    "stats": [
        {"id": "weapon_damage_die", "description": "Damage die used for the weapon or Unarmed Strike.", "pages": [50]},
        {"id": "attack_ability", "description": "Ability modifier used for attack and damage rolls.", "pages": [50]},
        {"id": "unarmed_strike_save_dc_ability", "description": "Ability modifier used for the save DC of Unarmed Strike's Grapple or Shove.", "pages": [50]},
        {"id": "jump_distance", "description": "The creature's jump distance.", "pages": [50]},
        {"id": "evasion", "description": "Evasion: on a Dexterity save for half damage, no damage on a success and half on a failure.", "pages": [51]}],
    "events": [
        {"id": "falls", "description": "The creature falls.", "pages": [51]},
        {"id": "bonus_action_taken", "description": "The creature takes a Bonus Action.", "pages": [52]}],
    "predicates": [
        {"id": "only_monk_weapons_or_unarmed", "description": "The creature is unarmed or wields only Monk weapons.", "type": "predicate", "pages": [50]},
        {"id": "attack_with_monk_weapon", "description": "The attack uses a Monk weapon.", "type": "predicate", "pages": [50]},
        {"id": "damage_reduced_to_zero", "description": "The triggering attack's damage was reduced to 0.", "type": "predicate", "pages": [51]},
        {"id": "spent_focus_point", "description": "A Focus Point was expended for the triggering use.", "type": "predicate", "pages": [51]},
        {"id": "used_feature_this_trigger", "description": "The creature used this feature (param) for the same trigger.", "params": ["feature"], "type": "predicate", "pages": [52]},
        {"id": "attack_from_feature", "description": "The attack or action was granted by this feature (param).", "params": ["feature"], "type": "predicate", "pages": [52]},
        {"id": "same_plane_as_target", "description": "The creature and the target are on the same plane of existence.", "type": "predicate", "pages": [52]}],
}

if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
