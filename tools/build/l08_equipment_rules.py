#!/usr/bin/env python3
"""L08 — Equipment rules: Armor Class, armor training, attunement, carrying capacity,
weapons, coins, selling, crafting nonmagical items.

Usage: python3 -I tools/build/l08_equipment_rules.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import build, extend_registries, glossary, md, ref_of, section, sidebar, write_entry  # noqa: E402

LOT = "L08"
SYS = "dnd5e/system/dnd5e"

REGISTRY = {
    "predicates": [
        {"id": "wearing_untrained_armor", "description": "The creature wears Light, Medium or Heavy armor it lacks training with.", "type": "predicate", "pages": [177]},
        {"id": "using_untrained_shield", "description": "The creature uses a Shield it lacks training with.", "type": "predicate", "pages": [177]},
        {"id": "moving_weight_over_carry", "description": "The creature drags, lifts or pushes weight above its carrying capacity.", "type": "predicate", "pages": [178]},
    ],
    "restrictions": [
        {"id": "cast_spells", "description": "The creature can't cast spells.", "pages": [177]},
        {"id": "shield_ac_bonus", "description": "The creature doesn't gain a Shield's AC bonus.", "pages": [177]},
    ],
}


def g(name, items, **kw):
    return glossary(name, "rule", LOT, items, **kw)


def entries():
    E = []
    E.append(g("Armor Class", [
        (None, "sys", [f"{SYS}#/core_die/rules/4"]),
        ("Your base AC calculation", "sys", [f"{SYS}#/levels/rules/7"]),
        ("If a rule gives you another base AC calculation", "rule", {"id": "one_base_ac", "choose_one": True}),
        ("*See also*", "ref", [ref_of("Attack Roll")])]))
    E.append(g("Armor Training", [
        (None, "fx", [{"op": "roll_mode", "mode": "disadvantage",
                       "rolls": ["d20_test.str", "d20_test.dex"], "when": {"pred": "wearing_untrained_armor"}},
                      {"op": "restrict", "restrictions": ["cast_spells"], "when": {"pred": "wearing_untrained_armor"}},
                      {"op": "restrict", "restrictions": ["shield_ac_bonus"],
                       "when": {"pred": "using_untrained_shield"}}]),
        ("*See also*", "ref", [ref_of("Disadvantage"), "dnd5e/rule/armor"])]))
    E.append(g("Attunement", [
        (None, "rule", {"id": "attunement", "max_items": 3}),
        ("*See also*", "ref", ["dnd5e/rule/magic-items"])]))
    E.append(g("Carrying Capacity", [
        (None, "table", {"id": "carrying_capacity", "caption": "Carrying Capacity",
                         "columns": ["Creature Size", "Carry", "Drag/Lift/Push"], "rows": [
                             ["Tiny", "Str. × 7.5 lb.", "Str. × 15 lb."], ["Small/Medium", "Str. × 15 lb.", "Str. × 30 lb."],
                             ["Large", "Str. × 30 lb.", "Str. × 60 lb."], ["Huge", "Str. × 60 lb.", "Str. × 120 lb."],
                             ["Gargantuan", "Str. × 120 lb.", "Str. × 240 lb."]]}),
        (None, "rule", {"id": "capacity_multipliers", "by_size": {
            "tiny": {"carry": 7.5, "drag_lift_push": 15}, "small": {"carry": 15, "drag_lift_push": 30},
            "medium": {"carry": 15, "drag_lift_push": 30}, "large": {"carry": 30, "drag_lift_push": 60},
            "huge": {"carry": 60, "drag_lift_push": 120}, "gargantuan": {"carry": 120, "drag_lift_push": 240}},
            "times": {"var": "ability_score.str"}, "unit": "pound"}),
        ("While dragging, lifting, or pushing weight", "fx", {"op": "speed", "movement": "walk", "mode": "min",
                                                               "value": 5,
                                                               "when": {"pred": "moving_weight_over_carry"}})]))
    E.append(g("Weapon", [(None, "rule", {"id": "weapon", "categories": ["simple", "martial"]}),
                          ("*See also*", "ref", ["dnd5e/rule/weapons"])]))

    E.append(build("rule", "coins", "Coins", section("Coins", 2), LOT, "Equipment/Coins", [
        (None, "sys", [f"{SYS}#/currency"]),
        ("A coin weighs about a third of an ounce", "sys", [f"{SYS}#/units/weight"])]))
    E.append(build("rule", "sidebar-selling-equipment", "Selling Equipment", sidebar("Selling Equipment"), LOT,
                   "Equipment", [
        (None, "rule", {"id": "sell_price", "equipment": 0.5, "trade_goods_and_valuables": 1}),
        ("“Magic Items” has prices for magic items.", "ref", ["dnd5e/rule/magic-item-rarity"])],
        facets={"sidebar": True}))
    E.append(build("rule", "crafting-nonmagical-items", "Crafting Nonmagical Items",
                   section("Crafting Nonmagical Items", 2), LOT, "Equipment/Crafting Nonmagical Items", [
        (None, "rule", {"id": "requirements", "needs": ["tools", "raw_materials", "time"],
                        "result_sells_at": "normal_price"}),
        ("### Tools", "ref", ["dnd5e/rule/tools"]),
        ("The GM assigns required tools", "md", md("craft_tools", "Which tool is required to make this item?",
                                                   "The GM assigns required tools for items not listed there.",
                                                   pages=[103])),
        ("You must use the required tool", "rule", {"id": "tool_proficiency", "crafter_and_helpers_proficient": True}),
        ("### Raw Materials", "rule", {"id": "materials", "cost_fraction": 0.5, "round": "down"}),
        ("The GM determines whether appropriate raw materials", "md", md(
            "materials_available", "Are appropriate raw materials available?", "The GM determines whether appropriate "
            "raw materials are available.", pages=[103])),
        ("### Time", "rule", {"id": "time", "days": {"op": "div", "args": [{"var": "item_cost_gp"}, 10], "round": "up"},
                              "hours_per_day": 8, "consecutive": False}),
        ("Characters can combine their efforts", "rule", {"id": "assistants", "time_divided_by": "workers",
                                                          "default_max_assistants": 1}),
        ("but the GM might allow more assistants", "md", md("more_assistants", "Allow more than one assistant?",
                                                            "Normally, only one other character can assist you, but "
                                                            "the GM might allow more assistants.", pages=[103]))]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY | {"variables": [{"id": "item_cost_gp", "description": "Purchase cost of the item in GP.", "type": "number", "pages": [103]}]}, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
