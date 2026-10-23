#!/usr/bin/env python3
"""L07 — Resources and rests: Short Rest, Long Rest, Hit Point Dice, the Resting sidebar.

Usage: python3 -I tools/build/l07_rests.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, extend_registries, glossary, ref_of, sidebar, write_entry  # noqa: E402

LOT = "L07"
C = lambda slug: f"dnd5e/condition/{slug}"  # noqa: E731

REGISTRY = {
    "pools": [
        {"id": "hit_point_dice", "name": "Hit Point Dice", "description": "Hit Point Dice available to spend (spent dice are tracked).", "pages": [183]},
    ],
    "variables": [
        {"id": "hit_point_die", "description": "The die type of one of the creature's Hit Point Dice.", "type": "dice", "pages": [183, 187]},
    ],
    "events": [
        {"id": "rest_interrupted", "description": "A rest is stopped by an interruption.", "type": "event", "pages": [185, 187]},
    ],
}


def g(name, items, **kw):
    return glossary(name, "rule", LOT, items, **kw)


def entries():
    E = []
    E.append(g("Hit Point Dice", [
        (None, "rule", {"id": "hit_point_dice", "pool": "hit_point_dice", "sets_hp_max": True,
                        "monsters_have_hit_dice": True}),
        ("A creature can spend Hit Dice during a Short Rest", "ref", [ref_of("Short Rest")]),
        ("*See also*", "ref", [ref_of("Short Rest")])]))
    E.append(g("Long Rest", [
        (None, "rule", {"id": "long_rest", "minimum_hours": 8, "sleep_hours_min": 6, "light_activity_hours_max": 2,
                        "available_to": "any_creature"}),
        ("During sleep, you have the Unconscious condition.", "fx", {"op": "apply_condition",
                                                                      "condition": C("unconscious"),
                                                                      "note": "While sleeping during the rest."}),
        ("After you finish a Long Rest, you must wait", "rule", {"id": "cooldown", "hours_between_long_rests": 16}),
        ("***Benefits of the Rest.***", "rule", {"id": "start_requires", "min_hit_points": 1}),
        ("**Regain All HP.**", "fx", {"op": "trigger", "event": {"event": "long_rest_finished"}, "then": [
            {"op": "heal", "amount": {"var": "hp_max"}, "note": "Regain all lost Hit Points."},
            {"op": "restore", "resource": "hit_point_dice", "amount": "all"}]}),
        ("**Regain All HP.**", "rule", {"id": "hp_max_restored", "reduced_hp_max_returns_to_normal": True}),
        ("**Ability Scores Restored.**", "rule", {"id": "ability_scores_restored", "reduced_scores_return": True}),
        ("**Exhaustion Reduced.**", "fx", {"op": "trigger", "event": {"event": "long_rest_finished"}, "then": [
            {"op": "remove_condition", "conditions": [C("exhaustion")], "levels": 1}]}),
        ("**Special Feature.**", "rule", {"id": "features_recharge", "event": "long_rest_finished"}),
        ("***Interrupting the Rest.***", "rule", {"id": "interruptions", "stopped_by": [
            "rolling_initiative", "casting_non_cantrip_spell", "taking_damage", "one_hour_of_physical_exertion"]}),
        ("If you rested at least 1 hour before the interruption", "rule", {
            "id": "partial", "if_rested_hours_at_least": 1, "gain": "short_rest_benefits"}),
        ("You can resume a Long Rest", "rule", {"id": "resume", "extra_hours_per_interruption": 1})]))
    E.append(g("Short Rest", [
        (None, "rule", {"id": "short_rest", "hours": 1, "activity": "no_more_strenuous_than_light",
                        "start_requires_min_hit_points": 1}),
        ("***Benefits of the Rest.***", "desc", None),
        ("**Spend Hit Point Dice.**", "fx", {"op": "activation", "name": "Spend a Hit Point Die", "cost": "none",
                                            "uses": {"resource": "hit_point_dice", "amount": 1},
                                            "then": [{"op": "heal", "amount": {"op": "max", "args": [1, {"op": "add",
                                                      "args": [{"var": "hit_point_die"}, {"var": "ability_mod.con"}]}]}}],
                                            "note": "Only when finishing a Short Rest; decide after each roll."}),
        ("**Special Feature.**", "rule", {"id": "features_recharge", "event": "short_rest_finished"}),
        ("***Interrupting the Rest.***", "rule", {"id": "interruptions", "stopped_by": [
            "rolling_initiative", "casting_non_cantrip_spell", "taking_damage"], "interrupted_benefits": "none"})]))
    E.append(build("rule", "sidebar-resting", "Resting", sidebar("Resting"), LOT, "Playing the Game/Damage and Healing", [
        (None, "ref", [ref_of("Short Rest"), ref_of("Long Rest")])], facets={"sidebar": True}))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
