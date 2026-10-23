#!/usr/bin/env python3
"""L03 — Conditions.

The 15 conditions of the Rules Glossary plus the "Condition" rule. A condition's effects
apply to the creature that has it ("you"); `direction: "against"` covers rolls other
creatures make against that creature. Effects that the condition grants only while it
lasts use no explicit duration: the engine removes them when the condition ends.

Usage: python3 -I tools/build/l03_conditions.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import extend_registries, glossary, md, write_entry  # noqa: E402

LOT = "L03"
C = lambda slug: f"dnd5e/condition/{slug}"  # noqa: E731
ALL_DAMAGE = ["acid", "bludgeoning", "cold", "fire", "force", "lightning", "necrotic", "piercing", "poison",
              "psychic", "radiant", "slashing", "thunder"]

REGISTRY = {
    "restrictions": [
        {"id": "see", "description": "The creature can't see.", "pages": [177]},
        {"id": "hear", "description": "The creature can't hear.", "pages": [181]},
        {"id": "speak", "description": "The creature can't speak.", "pages": [184]},
        {"id": "take_actions", "description": "The creature can't take any action.", "pages": [184]},
        {"id": "take_bonus_actions", "description": "The creature can't take any Bonus Action.", "pages": [184]},
        {"id": "take_reactions", "description": "The creature can't take any Reaction.", "pages": [184]},
        {"id": "maintain_concentration", "description": "The creature's Concentration is broken and can't be kept.", "pages": [184]},
        {"id": "increase_speed", "description": "The creature's Speed can't increase.", "pages": [182]},
        {"id": "move_closer_to_source", "description": "The creature can't willingly move closer to the source of the effect.", "pages": [182]},
        {"id": "attack_source", "description": "The creature can't attack the source of the effect.", "pages": [178]},
        {"id": "target_source_harmfully", "description": "The creature can't target the source with damaging abilities or magical effects.", "pages": [178]},
        {"id": "move_except_crawl", "description": "The creature's only movement options are to crawl or to stand up.", "pages": [186]},
        {"id": "age", "description": "The creature ceases aging.", "pages": [186]},
        {"id": "aware_of_surroundings", "description": "The creature is unaware of its surroundings.", "pages": [191]},
        {"id": "hold_items", "description": "The creature drops whatever it's holding.", "pages": [191]},
    ],
    "predicates": [
        {"id": "requires_sight", "description": "The ability check requires sight.", "type": "predicate", "pages": [177]},
        {"id": "requires_hearing", "description": "The ability check requires hearing.", "type": "predicate", "pages": [181]},
        {"id": "roller_is_source", "description": "The creature making the roll is the source of this effect (e.g. the charmer).", "type": "predicate", "pages": [178]},
        {"id": "target_is_source", "description": "The target of the roll is the source of this effect (e.g. the grappler).", "type": "predicate", "pages": [182]},
        {"id": "social_interaction", "description": "The ability check is made to interact socially with the affected creature.", "type": "predicate", "pages": [178]},
        {"id": "source_in_line_of_sight", "description": "The source of the effect is within the affected creature's line of sight.", "type": "predicate", "pages": [182]},
        {"id": "within_feet", "description": "A creature ('who': attacker, source...) is within 'feet' of the affected creature.", "params": ["who", "feet"], "type": "predicate", "pages": [186]},
        {"id": "can_be_seen_by", "description": "The roller ('who') can somehow see the affected creature.", "params": ["who"], "type": "predicate", "pages": [184]},
        {"id": "effect_requires_seen_target", "description": "The effect requires its target to be seen.", "type": "predicate", "pages": [184]},
        {"id": "speed_is_zero", "description": "The creature's Speed is 0.", "type": "predicate", "pages": [186]},
        {"id": "size_at_most_relative", "description": "The affected creature is Tiny or 'steps' or more sizes smaller than the other creature.", "params": ["steps"], "type": "predicate", "pages": [182]},
    ],
    "stats": [
        {"id": "d20_test", "description": "Every D20 Test the creature makes.", "pages": [181]},
        {"id": "weight", "description": "The creature's weight.", "pages": [186]},
    ],
    "variables": [
        {"id": "condition_level", "description": "Current level of a leveled condition (Exhaustion).", "params": ["condition"], "type": "number", "pages": [181]},
    ],
    "events": [
        {"id": "condition_ended", "description": "A condition ends on the creature (param: condition slug).", "params": ["condition"], "type": "event", "pages": [191]},
    ],
    "conditions": [{"id": c, "name": c.title(), "description": "Condition.", "ref": C(c), "pages": [p]} for c, p in [
        ("blinded", 177), ("charmed", 178), ("deafened", 181), ("exhaustion", 181), ("frightened", 182),
        ("grappled", 182), ("incapacitated", 184), ("invisible", 184), ("paralyzed", 186), ("petrified", 186),
        ("poisoned", 186), ("prone", 186), ("restrained", 187), ("stunned", 189), ("unconscious", 191)]],
}

INTRO = "While you have the"


def speed_zero():
    return [{"op": "speed", "movement": "walk", "mode": "set", "value": 0},
            {"op": "restrict", "restrictions": ["increase_speed"]}]


def incapacitated():
    return {"op": "apply_condition", "condition": C("incapacitated"),
            "note": "Lasts while the parent condition lasts."}


def auto_fail_str_dex():
    return {"op": "auto_result", "rolls": ["saving_throw.str", "saving_throw.dex"], "result": "fail"}


def against(mode, when=None):
    fx = {"op": "roll_mode", "mode": mode, "rolls": ["attack_roll"], "direction": "against"}
    if when:
        fx["when"] = when
    return fx


def own(mode, rolls=("attack_roll",), when=None):
    fx = {"op": "roll_mode", "mode": mode, "rolls": list(rolls), "direction": "own"}
    if when:
        fx["when"] = when
    return fx


def auto_crit_within_5():
    return {"op": "auto_result", "rolls": ["attack_roll"], "result": "critical_hit", "direction": "against",
            "when": {"pred": "within_feet", "args": {"who": "attacker", "feet": 5}},
            "note": "Only an attack roll that hits becomes a Critical Hit."}


def binary():
    return {"stacking": "binary"}


def entries():
    E = []
    cond = lambda name, items, **kw: glossary(name, "condition", LOT, items, data=kw.pop("data", binary()), **kw)  # noqa: E731

    E.append(cond("Blinded", [
        (None, "desc", None),
        ("***Can’t See.***", "fx", [{"op": "restrict", "restrictions": ["see"]},
                                    {"op": "auto_result", "rolls": ["ability_check"], "result": "fail",
                                     "when": {"pred": "requires_sight"}}]),
        ("***Attacks Affected.***", "fx", [against("advantage"), own("disadvantage")])]))
    E.append(cond("Charmed", [
        (None, "desc", None),
        ("***Can’t Harm the Charmer.***", "fx", {"op": "restrict",
                                                 "restrictions": ["attack_source", "target_source_harmfully"]}),
        ("***Social Advantage.***", "fx", {"op": "roll_mode", "mode": "advantage", "rolls": ["ability_check"],
                                          "direction": "against", "when": {"all": [{"pred": "roller_is_source"},
                                                                                   {"pred": "social_interaction"}]}})]))
    E.append(cond("Deafened", [
        (None, "desc", None),
        ("***Can’t Hear.***", "fx", [{"op": "restrict", "restrictions": ["hear"]},
                                     {"op": "auto_result", "rolls": ["ability_check"], "result": "fail",
                                      "when": {"pred": "requires_hearing"}}])]))
    level = {"var": "condition_level.exhaustion"}
    E.append(cond("Exhaustion", [
        (None, "desc", None),
        ("***Exhaustion Levels.***", "rule", {"id": "levels", "stacking": "levels", "gain_per_application": 1,
                                             "death_at_level": 6}),
        ("***D20 Tests Affected.***", "fx", {"op": "modifier", "stat": "d20_test", "mode": "add",
                                            "value": {"op": "mul", "args": [-2, level]}}),
        ("***Speed Reduced.***", "fx", {"op": "speed", "movement": "walk", "mode": "add",
                                       "value": {"op": "mul", "args": [-5, level]},
                                       "note": "Special speeds change by the same amount (Rules Glossary, Speed)."}),
        ("***Removing Exhaustion Levels.***", "fx", {"op": "trigger", "event": {"event": "long_rest_finished"},
                                                    "then": [{"op": "remove_condition",
                                                              "conditions": [C("exhaustion")], "levels": 1}]}),
        ("When your Exhaustion level reaches 0", "rule", {"id": "ends_at_zero", "ends_when_level": 0})],
        data={"stacking": "levels", "max_level": 6}))
    E.append(cond("Frightened", [
        (None, "desc", None),
        ("***Ability Checks and Attacks Affected.***", "fx",
         own("disadvantage", ("ability_check", "attack_roll"), {"pred": "source_in_line_of_sight"})),
        ("***Can’t Approach.***", "fx", {"op": "restrict", "restrictions": ["move_closer_to_source"]})]))
    E.append(cond("Grappled", [
        (None, "desc", None),
        ("***Speed 0.***", "fx", speed_zero()),
        ("***Attacks Affected.***", "fx", own("disadvantage", when={"not": {"pred": "target_is_source"}})),
        ("***Movable.***", "rule", {"id": "movable", "source_can_drag_or_carry": True,
                                    "extra_movement_cost_per_foot": 1,
                                    "no_extra_cost_if": {"pred": "size_at_most_relative", "args": {"steps": 2}}})],
        ))
    E.append(cond("Incapacitated", [
        (None, "desc", None),
        ("***Inactive.***", "fx", {"op": "restrict", "restrictions": ["take_actions", "take_bonus_actions",
                                                                       "take_reactions"]}),
        ("***No Concentration.***", "fx", {"op": "restrict", "restrictions": ["maintain_concentration"]}),
        ("***Speechless.***", "fx", {"op": "restrict", "restrictions": ["speak"]}),
        ("***Surprised.***", "fx", own("disadvantage", ("initiative",)))]))
    E.append(cond("Invisible", [
        (None, "desc", None),
        ("***Surprise.***", "fx", own("advantage", ("initiative",))),
        ("***Concealed.***", "rule", {"id": "concealed", "immune_to_effects_requiring_seen_target": True,
                                      "unless": {"pred": "can_be_seen_by", "args": {"who": "effect_creator"}},
                                      "worn_and_carried_equipment_concealed": True}),
        ("***Attacks Affected.***", "fx", [
            against("disadvantage", {"not": {"pred": "can_be_seen_by", "args": {"who": "attacker"}}}),
            {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "direction": "own",
             "when": {"not": {"pred": "can_be_seen_by", "args": {"who": "target"}}}}])]))
    E.append(cond("Paralyzed", [
        (None, "desc", None),
        ("***Incapacitated.***", "fx", incapacitated()),
        ("***Speed 0.***", "fx", speed_zero()),
        ("***Saving Throws Affected.***", "fx", auto_fail_str_dex()),
        ("***Attacks Affected.***", "fx", against("advantage")),
        ("***Automatic Critical Hits.***", "fx", auto_crit_within_5())]))
    E.append(cond("Petrified", [
        (None, "desc", None),
        ("***Turned to Inanimate Substance.***", "rule", {"id": "inanimate", "transformed_with":
                                                         "nonmagical_worn_and_carried_objects",
                                                         "substance": "solid_inanimate_usually_stone"}),
        ("***Turned to Inanimate Substance.***", "fx", [{"op": "modifier", "stat": "weight", "mode": "multiply",
                                                         "value": 10},
                                                        {"op": "restrict", "restrictions": ["age"]}]),
        ("***Incapacitated.***", "fx", incapacitated()),
        ("***Speed 0.***", "fx", speed_zero()),
        ("***Attacks Affected.***", "fx", against("advantage")),
        ("***Saving Throws Affected.***", "fx", auto_fail_str_dex()),
        ("***Resist Damage.***", "fx", {"op": "defense", "kind": "resistance", "damage_types": ALL_DAMAGE}),
        ("***Poison Immunity.***", "fx", {"op": "defense", "kind": "immunity", "conditions": [C("poisoned")]})]))
    E.append(cond("Poisoned", [
        (None, "desc", None),
        ("***Ability Checks and Attacks Affected.***", "fx", own("disadvantage", ("attack_roll", "ability_check")))]))
    E.append(cond("Prone", [
        (None, "desc", None),
        ("***Restricted Movement.***", "fx", [
            {"op": "restrict", "restrictions": ["move_except_crawl"]},
            {"op": "activation", "name": "Right yourself", "cost": "movement",
             "movement_cost": {"op": "div", "args": [{"var": "speed.walk"}, 2], "round": "down"},
             "requires": {"not": {"pred": "speed_is_zero"}},
             "then": [{"op": "remove_condition", "conditions": [C("prone")]}]}]),
        ("***Attacks Affected.***", "fx", [
            own("disadvantage"),
            against("advantage", {"pred": "within_feet", "args": {"who": "attacker", "feet": 5}}),
            against("disadvantage", {"not": {"pred": "within_feet", "args": {"who": "attacker", "feet": 5}}})])]))
    E.append(cond("Restrained", [
        (None, "desc", None),
        ("***Speed 0.***", "fx", speed_zero()),
        ("***Attacks Affected.***", "fx", [against("advantage"), own("disadvantage")]),
        ("***Saving Throws Affected.***", "fx", own("disadvantage", ("saving_throw.dex",)))]))
    E.append(cond("Stunned", [
        (None, "desc", None),
        ("***Incapacitated.***", "fx", incapacitated()),
        ("***Saving Throws Affected.***", "fx", auto_fail_str_dex()),
        ("***Attacks Affected.***", "fx", against("advantage"))]))
    E.append(cond("Unconscious", [
        (None, "desc", None),
        ("***Inert.***", "fx", [incapacitated(),
                                {"op": "apply_condition", "condition": C("prone"),
                                 "note": "Prone does not end with this condition: you remain Prone."},
                                {"op": "restrict", "restrictions": ["hold_items"]}]),
        ("***Speed 0.***", "fx", speed_zero()),
        ("***Attacks Affected.***", "fx", against("advantage")),
        ("***Saving Throws Affected.***", "fx", auto_fail_str_dex()),
        ("***Automatic Critical Hits.***", "fx", auto_crit_within_5()),
        ("***Unaware.***", "fx", {"op": "restrict", "restrictions": ["aware_of_surroundings"]})]))

    E.append(glossary("Condition", "rule", LOT, [
        (None, "sys", ["dnd5e/system/dnd5e#/registries/conditions"]),
        ("A condition doesn’t stack with itself", "rule", {"id": "no_self_stacking", "stacking": "binary",
                                                           "exceptions": [C("exhaustion")]})]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
