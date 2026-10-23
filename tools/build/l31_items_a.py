#!/usr/bin/env python3
"""L31 — Magic items A–Z, part 1 (Adamantine Armor … Cube of Force).

Usage: python3 -I tools/build/l31_items_a.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import NODES, find, write_entry, extend_registries  # noqa: E402
from magiclib import (ATTUNED, BONUS, CR, DAWN, HOLD, INHERIT, MAGIC, MI, SELF, SP, WEAR, WIELD, act, adv, area,  # noqa: E402
                      cast, charges, check, cond, creature, dmg, hours, immune_cond, item_nodes, md, mins, mod,
                      ref, resist, rounds, rows_of, save, sense, setv, speed, spells_table, tab, trig,
                      until_turn, while_)
from l31_registry import REGISTRY  # noqa: E402

LOT = "L31"
PLANES_TABLE = ["1d100", "Destination"]


def elemental_summoner(name, creature, where, extra_desc=None):
    """Bowl, Brazier and Censer: summon an elemental once per dawn."""
    items = [("^", "fx", act([{"op": "summon", "creature": CR(creature), "controller": "summoner", "initiative": "after_summoner",
                               "duration": hours(1), "note": f"Appears as close to the {where} as possible; understands your languages and obeys your commands."}],
                             freq=DAWN, requires={"pred": "within_feet_of_item", "args": {"feet": 5}})),
             ("^", "rule", {"id": "dismiss", "cost": "bonus_action", "ends_on": ["dismissed", "dies", "1_hour"]})]
    if extra_desc:
        items.append((extra_desc, "desc", None))
    return MI(name, items)


def entries():
    E = []
    E.append(MI("Adamantine Armor", [
        ("^", "desc", None),
        ("While you’re wearing it", "fx", {"op": "auto_result", "rolls": ["attack_roll"], "result": "hit", "direction": "against",
                                          "when": {"all": [WEAR, {"pred": "roll_is", "args": {"result": "critical_hit"}}]},
                                          "note": "Any Critical Hit against you becomes a normal hit."})]))
    E.append(MI("Ammunition, +1, +2, or +3", [
        ("^", "fx", [mod("attack_roll", BONUS, {"pred": "attack_uses_weapon", "args": THIS_AMMO}),
                     mod("damage_roll", BONUS, {"pred": "attack_uses_weapon", "args": THIS_AMMO})]),
        ("Once it hits a target", "rule", {"id": "single_use", "nonmagical_after_hit": True}),
        ("This ammunition is typically found", "rule", {"id": "quantity", "typical": [10, 20], "value": {"pieces": 10, "equals": "potion_of_same_rarity"}})]))
    slay = item_nodes("Ammunition of Slaying")
    E.append(MI("Ammunition of Slaying", [
        ("^", "md", md("slaying_type", "Which creature type does this ammunition slay? (choose or roll on the table)",
                       "which the GM chooses or determines randomly by rolling on the table below")),
        ("^", "fx", trig("deals_damage_with_item", save("con", 17, on_fail=dmg("6d10", "force"), half=True, target=INHERIT,
                                                         note="Extra damage; half as much on a success."),
                         condition={"pred": "creature_type_chosen", "args": {"choice": "slaying_type"}})),
        ("After dealing its extra damage", "rule", {"id": "single_use", "nonmagical_after_extra_damage": True}),
        ("| **1d100**", "table", tab("Ammunition of Slaying", ["1d100", "Creature Type", "1d100", "Creature Type"], rows_of(slay)))]))
    E.append(MI("Amulet of Health", [("^", "fx", setv("ability_score.con", 19, WEAR, note="No effect if your Constitution is already 19 or higher (set never lowers)."))]))
    E.append(MI("Amulet of Proof against Detection and Location", [
        ("^", "fx", {"op": "restrict", "restrictions": ["targeted_by_divination", "detected_or_viewed_by_magic"], "when": WEAR,
                     "note": "Can't be targeted by Divination spells or perceived through magical scrying sensors unless you allow it."})]))
    planes = item_nodes("Amulet of the Planes")
    E.append(MI("Amulet of the Planes", [
        ("^", "fx", act(check("int", 15, skill="arcana", on_success=cast("Plane Shift"),
                              on_fail=[{"op": "move", "mode": "teleport", "target": area("emanation", 15, origin="self"),
                                        "note": "You and each creature and object within 15 feet travel to a random destination (table)."}]),
                        requires=WEAR, note="Name a familiar location on another plane.")),
        ("| **1d100**", "table", tab("Amulet of the Planes", PLANES_TABLE, rows_of(planes)))]))
    E.append(MI("Animated Shield", [
        ("^", "fx", act({"op": "modifier", "stat": "ac", "mode": "add", "value": {"var": "shield_ac_bonus"},
                         "duration": mins(1), "note": "The Shield protects you as if wielded, leaving your hands free."},
                        cost="bonus_action", requires=HOLD)),
        ("^", "rule", {"id": "animate", "ends_on": ["bonus_action", "dies", "incapacitated"], "duration_minutes": 1,
                       "falls": "to the ground or into a free hand"})]))
    # the PDF prints the levers table after Armor of Resistance (column flow); lever 5 "Down" is a paragraph
    lv = find("Apparatus of the Crab Levers", 5)
    levers = [NODES[lv]] + [n for n in NODES[lv + 1:lv + 14] if n.type == "t" or n.text.startswith("Each extended claw")]
    lever_rows = [r for r in rows_of(levers)]
    lever_rows[4] = lever_rows[4] + [levers[6].text.replace("*", "")] if len(lever_rows[4]) == 2 else lever_rows[4]
    E.append(MI("Apparatus of the Crab", [
        ("^", "fx", check("int", 20, skill="investigation", on_success=ref("dnd5e/magic-item/apparatus-of-the-crab", note="Finds the hidden catch."))),
        ("^", "rule", {"id": "barrel", "weight_lb": 500, "occupants": 2, "occupant_max_size": "medium", "levers": 10}),
        ("The *Apparatus of the Crab* is a Large", "rule", {"id": "object", "size": "large", "ac": 20, "hp": 200,
                                                           "speed": {"walk": 30, "swim": 30, "legs_retracted": 0},
                                                           "immunities": ["poison", "psychic"]}),
        ("To be used as a vehicle", "rule", {"id": "vehicle", "pilots": 1, "airtight_when_closed": True,
                                             "air_hours": 10, "air_divided_by_breathers": True}),
        ("The apparatus floats on water.", "rule", {"id": "depth", "floats": True, "max_depth_feet": 900,
                                                     "below": {"damage": "2d6", "damage_type": "bludgeoning", "per": "minute"}}),
        ("A creature in the compartment", "rule", {"id": "levers", "action": "dnd5e/action/utilize", "levers_per_action": 2,
                                                   "return_to_neutral": True}),
        ("##### Apparatus of the Crab Levers", "table", tab("Apparatus of the Crab Levers", ["Lever", "Up", "Down"], lever_rows)),
        ("| 5 |", "fx", [{"op": "attack", "attack_type": "melee", "bonus": 8, "on_hit": [dmg("2d6", "bludgeoning")],
                          "note": "Lever 5 up: each extended claw; reach 5 ft."}]),
        ("Each extended claw makes the following melee attack: +8 to hit, reach 5 ft. *Hit:* The target", "fx", [
            {"op": "attack", "attack_type": "melee", "bonus": 8,
             "on_hit": [cond("grappled", params={"escape_dc": 15})], "note": "Lever 5 down: each extended claw; reach 5 ft."}])],
        extra=levers))
    E.append(MI("Armor, +1, +2, or +3", [("^", "fx", mod("ac", BONUS, WEAR))]))
    E.append(MI("Armor of Invulnerability", [
        ("^", "fx", resist(["bludgeoning", "piercing", "slashing"], WEAR)),
        ("***Metal Shell.***", "fx", act(resist(["bludgeoning", "piercing", "slashing"], kind="immunity",
                                                duration={"kind": "minutes", "amount": 10, "ends_on": [{"event": "unequips_item"}]}),
                                         freq=DAWN, requires=WEAR, name="Metal Shell"))]))
    res = item_nodes("Armor of Resistance", stop="Apparatus of the Crab Levers")
    E.append(MI("Armor of Resistance", [
        ("^", "md", md("resistance_type", "Which damage type does the armor resist? (choose or roll 1d10)",
                       "The GM chooses the type or determines it randomly by rolling on the following table.")),
        ("^", "fx", resist([{"var": "chosen.resistance_type"}], WEAR)),
        ("| **1d10**", "table", tab("Armor of Resistance", ["1d10", "Damage Type", "1d10", "Damage Type"], rows_of(res)))],
        nodes=res))
    E.append(MI("Armor of Vulnerability", [
        ("^", "md", md("resistance_type", "Which of Bludgeoning, Piercing or Slashing does the armor resist?",
                       "The GM chooses the type or determines it randomly.",
                       options=["bludgeoning", "piercing", "slashing"])),
        ("^", "fx", resist([{"var": "chosen.resistance_type"}], WEAR)),
        ("***Curse.***", "ref", ["dnd5e/rule/cursed-items"]),
        ("***Curse.***", "rule", {"id": "curse", "revealed_by": [SP("Identify"), "attunement"], "ends_by": [SP("Remove Curse")],
                                  "removing_item_ends": False}),
        ("***Curse.***", "fx", resist(["bludgeoning", "piercing", "slashing"], kind="vulnerability", when=ATTUNED,
                                      note="Two of the three types: those other than the one the armor resists."))]))
    E.append(MI("Arrow-Catching Shield", [
        ("^", "fx", mod("ac", 2, {"all": [WIELD, {"pred": "attack_is_ranged"}]}, note="In addition to the Shield's normal bonus.")),
        ("Whenever an attacker makes", "fx", trig({"event": "ranged_attack_against_creature_within_feet", "whose": "any", "which": "each"},
                                                  ref("dnd5e/magic-item/arrow-catching-shield", note="You become the target of the attack instead."),
                                                  cost="reaction", optional=True,
                                                  condition={"pred": "within_feet", "args": {"feet": 5}}))]))
    beans = item_nodes("Bag of Beans")
    E.append(MI("Bag of Beans", [
        ("^", "rule", {"id": "beans", "count": "3d4", "bag_weight_lb": 0.5, "nonmagical_when_empty": True}),
        ("If you dump one or more beans", "fx", save("dex", 15, on_fail=dmg("5d4", "force"), half=True,
                                                     target=area("sphere", 10, origin="point"), note="Includes you; dumped beans are destroyed.")),
        ("If you remove a bean from the bag", "rule", {"id": "planting", "requires": ["dirt_or_sand", "water"], "delay_minutes": 1}),
        ("If you remove a bean from the bag", "md", md("bean_effect", "Choose an effect from the table or roll 1d100.",
                                                       "The GM can choose an effect from the following table or determine it randomly.")),
        ("| **1d100**", "table", tab("Bag of Beans", ["1d100", "Effect"], rows_of(beans))),
        ("| **1d100**", "ref", [CR("Treant"), CR("Shrieker Fungus"), CR("Bulette"), CR("Mummy"), CR("Mummy Lord")])]))
    E.append(MI("Bag of Devouring", [
        ("^", "desc", None),
        ("The extradimensional creature", "rule", {"id": "devour", "animal_or_vegetable_matter": "devoured",
                                                   "pull_in_chance_percent": 50,
                                                   "escape": {"cost": "action", "check": "str.athletics", "dc": 15},
                                                   "pull_out": {"cost": "action", "check": "str.athletics", "dc": 20},
                                                   "starts_turn_inside": "devoured"}),
        ("Inanimate objects can be stored", "rule", {"id": "storage", "cubic_feet": 1, "daily": "objects_sent_to_another_plane"}),
        ("Inanimate objects can be stored", "md", md("devour_plane", "When during the day, and to which plane, are the objects sent?",
                                                     "The GM determines the time and plane.")),
        ("If the bag is pierced or torn", "rule", {"id": "destroyed", "on": ["pierced", "torn"], "contents_to": "astral_plane_random"})]))
    E.append(MI("Bag of Holding", [
        ("^", "rule", {"id": "capacity", "interior_feet": [2, 2, 4], "max_lb": 500, "max_cubic_feet": 64, "weight_lb": 5,
                       "retrieve": "dnd5e/action/utilize"}),
        ("If the bag is overloaded", "rule", {"id": "destroyed", "on": ["overloaded", "pierced", "torn"], "contents_to": "astral_plane",
                                              "inside_out": "spills_unharmed", "air_minutes": 10, "air_divided_by_breathers": True}),
        ("Placing a *Bag of Holding*", "rule", {"id": "extradimensional_conflict",
                                                "with": ["dnd5e/magic-item/handy-haversack", "dnd5e/magic-item/portable-hole"],
                                                "both_destroyed": True, "gate": "astral_plane", "one_way": True}),
        ("Placing a *Bag of Holding*", "fx", {"op": "move", "mode": "teleport", "target": area("sphere", 10, origin="point"),
                                              "note": "Each creature within the Sphere is sucked to a random location on the Astral Plane."})]))
    tricks = item_nodes("Bag of Tricks")

    def tricks_rows(cap):
        i = next(k for k, n in enumerate(tricks) if n.text == cap)
        return rows_of([n for n in tricks[i + 1:i + 6] if n.type == "t"])
    E.append(MI("Bag of Tricks", [
        ("^", "desc", None),
        ("You can take a Magic action to pull", "fx", act({"op": "choice", "id": "creature", "choose": 1,
                                                          "note": "Thrown up to 20 feet; roll 1d8 on the table of the bag's color.",
                                                          "options": [{"id": f"{color.lower()}_{r[k]}", "label": f"{color} {r[k]}: {r[k + 1]}",
                                                                       "effects": [{"op": "summon", "creature": CR(r[k + 1]), "controller": "summoner",
                                                                                    "initiative": "after_summoner",
                                                                                    "duration": {"kind": "until_event", "until": {"event": "dawn"},
                                                                                                 "ends_on": [{"event": "drops_to_0_hp"}]}}]}
                                                                      for color in ("Gray", "Rust", "Tan")
                                                                      for r in tricks_rows(f"{color} Bag of Tricks") for k in (0, 2)]},
                                                         freq={"count": 3, "per": "dawn"})),
        ("The creature is Friendly", "rule", {"id": "command", "attitude": "friendly", "cost": "bonus_action",
                                              "no_orders": "acts_per_nature"}),
        ("##### Gray Bag of Tricks", "table", tab("Gray Bag of Tricks", ["1d8", "Creature", "1d8", "Creature"], tricks_rows("Gray Bag of Tricks"))),
        ("##### Rust Bag of Tricks", "table", tab("Rust Bag of Tricks", ["1d8", "Creature", "1d8", "Creature"], tricks_rows("Rust Bag of Tricks"))),
        ("##### Tan Bag of Tricks", "table", tab("Tan Bag of Tricks", ["1d8", "Creature", "1d8", "Creature"], tricks_rows("Tan Bag of Tricks")))]))
    E.append(MI("Bead of Force", [
        ("^", "rule", {"id": "bead", "weight_oz": 1, "found_together": "1d4 + 4"}),
        ("You can take a Magic action to throw", "fx", act([
            save("dex", 15, on_fail=dmg("5d4", "force"), target=area("sphere", 10, origin="point"),
                 note="Thrown up to 60 feet; the bead is destroyed."),
            {"op": "reference", "rule": "dnd5e/magic-item/bead-of-force", "duration": mins(1),
             "note": "A sphere of force encloses the area: creatures that failed and are wholly inside are trapped; others are pushed out. Only breathable air passes."}])),
        ("An enclosed creature can take", "rule", {"id": "rolling", "action": "dnd5e/action/utilize", "move": "half_speed",
                                                   "carried_weight_lb": 1})]))
    E.append(MI("Bead of Nourishment", [("^", "rule", {"id": "nourishment", "equals": "dnd5e/gear/rations", "days": 1})]))
    E.append(MI("Belt of Dwarvenkind", [
        ("^", "desc", None),
        ("**Dwarvish.**", "fx", {"op": "proficiency", "category": "language", "items": ["dwarvish"], "when": WEAR}),
        ("**Friend of Dwarvenkind.**", "fx", adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "persuasion"}},
                                                                          {"pred": "interacting_with", "args": {"creatures": ["dwarves", "duergar"]}}]})),
        ("**Toughness.**", "fx", mod("ability_score.con", 2, WEAR, note="To a maximum of 20.")),
        ("In addition, while attuned", "rule", {"id": "beard", "chance_percent": 50, "when": "each dawn"}),
        ("If you aren’t a dwarf or duergar", "desc", None),
        ("**Darkvision.**", "fx", sense("darkvision", 60, {"all": [WEAR, {"not": {"pred": "is_species", "args": {"species": ["dwarf", "duergar"]}}}]})),
        ("**Resilience.**", "fx", resist("poison", {"all": [WEAR, {"not": {"pred": "is_species", "args": {"species": ["dwarf", "duergar"]}}}]})),
        ("You also have Advantage", "fx", adv("saving_throw", {"all": [WEAR, {"pred": "save_against_condition", "args": {"condition": "poisoned"}}]}))]))
    giant = item_nodes("Belt of Giant Strength")
    E.append(MI("Belt of Giant Strength", [
        ("^", "fx", setv("ability_score.str", {"var": "item_variant_score"}, WEAR,
                         note="No effect if your Strength is already equal or greater (set never lowers).")),
        ("| **Belt**", "table", tab("Belt of Giant Strength", ["Belt", "Str.", "Rarity"], rows_of(giant)))],
        data={"item": {"variants": [{"variant": r[0].replace("Belt of Giant Strength ", ""), "score": int(r[1]),
                                     "rarity": r[2].lower().replace(" ", "_")} for r in rows_of(giant)]}}))
    E.append(MI("Berserker Axe", [
        ("^", "fx", [mod("attack_roll", 1, WIELD), mod("damage_roll", 1, WIELD), mod("hp_max", {"var": "level"}, ATTUNED)]),
        ("***Curse.***", "ref", ["dnd5e/rule/cursed-items"]),
        ("***Curse.***", "fx", [adv("attack_roll", {"all": [ATTUNED, {"not": {"pred": "attack_uses_weapon", "args": {"item": "this"}}}]},
                                    mode="disadvantage")]),
        ("***Curse.***", "rule", {"id": "curse", "unwilling_to_part": True}),
        ("Whenever another creature damages you", "fx", trig({"event": "damage_taken", "which": "each"},
                                                            save("wis", 15, on_fail={"op": "reference", "rule": "dnd5e/magic-item/berserker-axe",
                                                                                     "note": "You go berserk."}),
                                                            condition=all_possessed())),
        ("Whenever another creature damages you", "rule", {"id": "berserk_end", "ends": "turn_start with no creature you can see or hear within 60 feet"}),
        ("While berserk", "rule", {"id": "berserk", "target": "nearest creature you can see or hear", "ties": "random",
                                   "each_turn": ["move_closest", "dnd5e/action/attack"], "retarget": "next nearest"})]))
    E.append(MI("Boots of Elvenkind", [
        ("^", "rule", {"id": "silent_steps", "when": "worn"}),
        ("^", "fx", adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "stealth"}}]}))]))
    E.append(MI("Boots of Levitation", [("^", "fx", act(cast("Levitate", target=SELF), requires=WEAR))]))
    E.append(MI("Boots of Speed", [
        ("^", "fx", act([{"op": "speed", "movement": "walk", "mode": "multiply", "value": 2, "duration": while_({"pred": "effect_active"})},
                         adv("attack_roll", {"pred": "attack_is_opportunity_attack"}, mode="disadvantage", direction="against")],
                        cost="bonus_action", requires=WEAR, note="Clicking the heels again ends the effect.")),
        ("When you’ve used the boots’ property", "rule", {"id": "limit", "total_minutes": 10, "recovers_on": "long_rest"})]))
    E.append(MI("Boots of Striding and Springing", [
        ("^", "fx", [speed("walk", 30, mode="min", when=WEAR),
                     {"op": "restrict", "restrictions": ["speed_reduced_by_encumbrance_or_heavy_armor"], "when": WEAR}]),
        ("Once on each of your turns", "fx", {"op": "activation", "cost": "none", "frequency": {"count": 1, "per": "turn"},
                                              "movement_cost": 10, "requires": WEAR,
                                              "then": [{"op": "move", "mode": "jump", "distance_feet": 30}]})]))
    E.append(MI("Boots of the Winterlands", [
        ("^", "desc", None),
        ("***Cold Resistance.***", "fx", resist("cold", WEAR)),
        ("***Cold Resistance.***", "rule", {"id": "cold_tolerance", "min_fahrenheit": 0}),
        ("***Winter Strider.***", "fx", {"op": "modifier", "stat": "ignores_difficult_terrain", "mode": "set", "value": 1,
                                         "when": {"all": [WEAR, {"pred": "terrain_from", "args": {"source": ["ice", "snow"]}}]}})]))
    E.append(elemental_summoner("Bowl of Commanding Water Elementals", "Water Elemental", "bowl", "The bowl is about 1 foot"))
    E.append(MI("Bracers of Archery", [
        ("^", "fx", [{"op": "proficiency", "category": "weapon", "items": ["dnd5e/weapon/longbow", "dnd5e/weapon/shortbow"], "when": WEAR},
                     mod("damage_roll", 2, {"all": [WEAR, {"pred": "attack_uses_weapon", "args": {"weapon": ["longbow", "shortbow"]}}]})])]))
    E.append(MI("Bracers of Defense", [
        ("^", "fx", mod("ac", 2, {"all": [WEAR, {"not": {"pred": "wearing_armor_any"}}, {"not": {"pred": "using_shield"}}]}))]))
    E.append(elemental_summoner("Brazier of Commanding Fire Elementals", "Fire Elemental", "brazier"))
    E.append(MI("Brooch of Shielding", [
        ("^", "fx", [resist("force", WEAR),
                     {"op": "defense", "kind": "immunity", "damage_types": ["force"], "note": "Damage from the Magic Missile spell.",
                      "when": {"all": [WEAR, {"pred": "damage_from_spell", "args": {"spell": "magic-missile"}}]}}])]))
    E.append(MI("Broom of Flying", [
        ("^", "fx", act(speed("fly", 50, hover=True, duration=while_({"pred": "riding_item", "args": {"item": "this"}})),
                        note="Stand astride it; it stops hovering when you land or stop riding it.")),
        ("^", "rule", {"id": "capacity", "max_lb": 400, "heavy_over_lb": 200, "heavy_fly_speed": 30}),
        ("As a Magic action, you can send", "fx", act({"op": "move", "mode": "move", "target": {"kind": "object"},
                                                      "note": "The broom travels alone to a familiar named location within 1 mile."})),
        ("As a Magic action, you can send", "rule", {"id": "recall", "cost": "action", "command_word": True, "range_miles": 1})]))
    inv = item_nodes("Candle of Invocation")
    E.append(MI("Candle of Invocation", [
        ("^", "rule", {"id": "burn", "light_cost": "dnd5e/action/magic", "burn_hours": 4, "snuff_saves_time": True, "increment_minutes": 1}),
        ("While lit, the candle sheds", "fx", [adv("d20_test", {"pred": "in_item_light", "args": THIS_ITEM}),
                                              {"op": "modifier", "stat": "spell_slot_cost", "mode": "set", "value": 0,
                                               "when": {"all": [{"pred": "in_item_light", "args": THIS_ITEM},
                                                                {"pred": "class_is", "args": {"classes": ["cleric", "druid"]}},
                                                                {"pred": "spell_level_is", "args": {"level": 1}}]},
                                               "note": "Prepared level 1 spells without expending spell slots."}]),
        ("While lit, the candle sheds", "rule", {"id": "light", "dim_feet": 30, "rules": ["dnd5e/rule/dim-light"]}),
        ("Alternatively, when you light", "fx", cast("Gate", note="Only when first lit; destroys the candle.")),
        ("Alternatively, when you light", "md", md("gate_plane", "Which Outer Plane does the portal link to? (choose or roll 1d100)",
                                                  "chosen by the GM or determined by rolling on the following table")),
        ("| **1d100**", "table", tab("Candle of Invocation", ["1d100", "Outer Plane", "1d100", "Outer Plane"], rows_of(inv)))]))
    E.append(MI("Cape of the Mountebank", [
        ("^", "fx", act(cast("Dimension Door"), freq=DAWN, requires=WEAR)),
        ("When you teleport with that spell", "rule", {"id": "smoke", "obscurement": "dnd5e/rule/lightly-obscured",
                                                       "where": "space_left", "until": "end of your next turn"})]))
    carpet = item_nodes("Carpet of Flying")
    E.append(MI("Carpet of Flying", [
        ("^", "fx", act(speed("fly", {"var": "item_variant_fly_speed"}, hover=True),
                        note="Command word; moves at your direction while you are within 30 feet.")),
        ("Four sizes of *Carpet of Flying*", "md", md("carpet_size", "Which size is this carpet? (choose or roll 1d100)",
                                                      "The GM chooses the size of a given carpet or determines it randomly")),
        ("Four sizes of *Carpet of Flying*", "rule", {"id": "overload", "max_multiplier": 2, "over_capacity_fly_speed": 0.5}),
        ("| **1d100**", "table", tab("Carpet of Flying", ["1d100", "Size", "Capacity", "Fly Speed"], rows_of(carpet)))]))
    E.append(elemental_summoner("Censer of Controlling Air Elementals", "Air Elemental", "censer"))
    E.append(MI("Chime of Opening", [
        ("^", "fx", act(cast("Knock"), uses=1)),
        ("^", "rule", {"id": "chime", "length_feet": 1, "weight_lb": 1, "audible_feet": 300}),
        ("The chime can be used 10 times", "fx", charges(10)),
        ("The chime can be used 10 times", "rule", {"id": "cracks", "after_uses": 10, "useless": True})]))
    E.append(MI("Circlet of Blasting", [("^", "fx", act(cast("Scorching Ray", attack=5), freq=DAWN, requires=WEAR))]))
    E.append(MI("Cloak of Arachnida", [
        ("^", "desc", None),
        ("***Poison Resistance.***", "fx", resist("poison", WEAR)),
        ("***Spider Climb.***", "fx", [speed("climb", 0, mode="equal_to_walk", when=WEAR),
                                       {"op": "modifier", "stat": "spider_climb", "mode": "set", "value": 1, "when": WEAR}]),
        ("***Spider Walk.***", "fx", {"op": "restrict", "restrictions": ["caught_in_webs"], "when": WEAR,
                                      "note": "Moves through webs as if they were Difficult Terrain."}),
        ("***Web.***", "fx", act(cast("Web", dc=13, note="Fills twice its normal area."), freq=DAWN, requires=WEAR))]))
    E.append(MI("Cloak of Displacement", [
        ("^", "fx", adv("attack_roll", {"all": [WEAR, {"not": {"pred": "speed_is_zero"}},
                                                {"not": {"pred": "took_damage_since_turn_start"}}]},
                        mode="disadvantage", direction="against",
                        note="Suppressed after you take damage until the start of your next turn, and while your Speed is 0."))]))
    E.append(MI("Cloak of Elvenkind", [
        ("^", "fx", [adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "perception"}}]},
                         mode="disadvantage", direction="against", note="Checks made to perceive you."),
                     adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "stealth"}}]})])]))
    E.append(MI("Cloak of Invisibility", [
        ("^", "fx", [charges(3, "1d3"),
                     act(cond("invisible", hours(1, ends_on=[{"event": "unequips_item"}, {"event": "hood_lowered"}])),
                         uses=1, requires=WEAR, note="Pulling the hood down (no action) ends it early.")])]))
    E.append(MI("Cloak of Protection", [("^", "fx", [mod("ac", 1, WEAR), mod("saving_throw", 1, WEAR)])]))
    E.append(MI("Cloak of the Bat", [
        ("^", "fx", [adv("ability_check", {"all": [WEAR, {"pred": "check_uses_skill", "args": {"skill": "stealth"}}]}),
                     speed("fly", 40, when={"all": [WEAR, {"any": [{"pred": "in_dim_light"}, {"pred": "in_darkness"}]},
                                                    {"pred": "gripping_item", "args": THIS_ITEM}]})]),
        ("While wearing the cloak in an area", "fx", act(cast("Polymorph", target=SELF,
                                                              note="Into a Bat (dnd5e/creature/bat). You keep your Intelligence, Wisdom and Charisma scores."),
                                                         freq=DAWN, requires={"all": [WEAR, {"any": [{"pred": "in_dim_light"}, {"pred": "in_darkness"}]}]}))]))
    E.append(MI("Cloak of the Manta Ray", [
        ("^", "fx", [{"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1, "when": WEAR},
                     speed("swim", 60, when=WEAR)])]))
    E.append(MI("Crystal Ball", [("^", "fx", act(cast("Scrying", dc=17), requires=HOLD))]))
    E.append(MI("Crystal Ball of Mind Reading", [
        ("^", "fx", [act(cast("Scrying", dc=17), requires=HOLD),
                     act(cast("Detect Thoughts", dc=17,
                              note="No Concentration needed. Targets creatures you can see within 30 feet of the Scrying sensor; ends if Scrying ends."),
                         requires=HOLD)])]))
    E.append(MI("Crystal Ball of Telepathy", [
        ("^", "fx", [act(cast("Scrying", dc=17), requires=HOLD),
                     {"op": "reference", "rule": "dnd5e/rule/telepathy", "note": "With creatures you can see within 30 feet of the sensor."},
                     act(cast("Suggestion", dc=17, note="No Concentration needed. Through the sensor; ends if Scrying ends."),
                         freq=DAWN, requires=HOLD)])]))
    E.append(MI("Crystal Ball of True Seeing", [
        ("^", "fx", [act(cast("Scrying", dc=17), requires=HOLD),
                     sense("truesight", 120, note="Centered on the Scrying sensor.")])]))
    cube = item_nodes("Cube of Force")
    E.append(MI("Cube of Force", [
        ("^", "fx", spells_table([("Mage Armor", 1), ("Shield", 1), ("Tiny Hut", 3), ("Private Sanctum", 4),
                                  ("Resilient Sphere", 4), ("Wall of Force", 5)], dc=17)),
        ("The cube starts with 10 charges", "fx", charges(10, "1d6")),
        ("##### Cube of Force Faces", "table", tab("Cube of Force Faces", ["Spell", "Charge Cost"], rows_of(cube)))]))
    return E


THIS_AMMO = {"item": "this"}
THIS_ITEM = {"item": "this"}


def all_possessed():
    return {"pred": "possesses_item", "args": {"item": "this"}}


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
