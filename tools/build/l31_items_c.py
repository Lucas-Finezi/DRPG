#!/usr/bin/env python3
"""L31 — Magic items A–Z, part 3 (Headband of Intellect … Nine Lives Stealer) and the Avatar of
Death stat block.

Usage: python3 -I tools/build/l31_items_c.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from entrylib import extend_registries, write_entry  # noqa: E402
from magiclib import (ATTUNED, DAWN, DIES, HOLD, INHERIT, MI, SELF, SP, THIS, WEAR, WIELD, act, adv, area,  # noqa: E402
                      cast, charges, check, cond, creature, dmg, hours, item_nodes, md, mins, mod, ref, resist,
                      rows_of, save, sense, setv, speed, spells_table, tab, trig, until_turn, while_)
from l31_registry import REGISTRY  # noqa: E402
from statblock import creature_entry  # noqa: E402

LOT = "L31"
EACH_END = {"on": {"event": "turn_end", "whose": "target", "which": "each"}, "ends": "effect_on_self"}
ORBIT = {"pred": "item_orbiting", "args": THIS}


def plus_weapon(n):
    return [mod("attack_roll", n, WIELD), mod("damage_roll", n, WIELD)]


def hit_with_this(*preds):
    return {"all": [{"pred": "attack_uses_weapon", "args": THIS}, *preds]}


def type_in(*types):
    return {"pred": "creature_type_in", "args": {"types": list(types)}}


def manual(name, ability):
    return MI(name, [
        ("^", "fx", act(mod(f"ability_score.{ability}", 2, note="To a maximum of 30."), cost="none",
                        action=None, note="48 hours of study over 6 days or fewer.")),
        ("^", "rule", {"id": "study", "hours": 48, "within_days": 6, "max_score": 30,
                       "then": "loses its magic", "regains_after_years": 100})])


def horseshoes(name, effects):
    return MI(name, [
        ("^", "rule", {"id": "set", "count": 4, "affix": "dnd5e/action/magic", "remove": "dnd5e/action/magic",
                       "creature": "horse or similar creature"}),
        ("While all four", "fx", effects)])


def ioun(label, effects):
    return (f"***{label}", "fx", effects)


def entries():
    E = []
    E.append(MI("Headband of Intellect", [("^", "fx", setv("ability_score.int", 19, WEAR, note="No effect if your Intelligence is already 19 or higher."))]))
    E.append(MI("Helm of Brilliance", [
        ("^", "rule", {"id": "gems", "diamond": "1d10", "ruby": "2d10", "fire_opal": "3d10", "opal": "4d10",
                       "pried_gem_crumbles": True, "no_gems": "loses its magic"}),
        ("You gain the following benefits", "desc", None),
        ("***Diamond Light.***", "fx", trig({"event": "turn_start", "whose": "any", "which": "each"}, dmg("1d6", "radiant"),
                                            condition={"all": [WEAR, {"pred": "item_has_gem", "args": {"gem": "diamond"}},
                                                               type_in("undead"), {"pred": "within_feet", "args": {"feet": 30}}]},
                                            note="Any Undead that starts its turn in the 30-foot Emanation.")),
        ("***Diamond Light.***", "rule", {"id": "diamond_light", "emanation_feet": 30, "dim_light_when_undead_present": True}),
        ("***Fire Opal Flames.***", "fx", act(trig("hits_with_attack_roll", dmg("1d6", "fire", target=INHERIT),
                                                   condition={"pred": "attack_uses_weapon", "args": {"item": "blazing_weapon"}}),
                                              requires={"all": [WEAR, {"pred": "item_has_gem", "args": {"gem": "fire_opal"}}]},
                                              note="One held weapon bursts into flames until extinguished (Bonus Action), dropped or stowed.")),
        ("***Fire Opal Flames.***", "rule", {"id": "flame_light", "bright_feet": 10, "dim_feet": 10, "harmless_to_you_and_weapon": True}),
        ("***Ruby Resistance.***", "fx", resist("fire", {"all": [WEAR, {"pred": "item_has_gem", "args": {"gem": "ruby"}}]})),
        ("***Spells.***", "fx", [act(cast(s, dc=18, note=f"Destroys one {g} from the helm."), requires=WEAR)
                                 for s, g in (("Daylight", "opal"), ("Fireball", "fire opal"), ("Prismatic Spray", "diamond"), ("Wall of Fire", "ruby"))]),
        ("***Taking Fire Damage.***", "fx", trig({"event": "damage_taken", "which": "each"},
                                                 {"op": "choice", "id": "d20", "choose": 1, "note": "Roll 1d20.", "options": [
                                                     {"id": "one", "label": "1", "effects": [
                                                         save("dex", 17, on_fail=dmg({"var": "item_gems"}, "radiant"), target=area("emanation", 60, origin="self"),
                                                              note="Beams from the remaining gems; then the helm is destroyed."),
                                                         {"op": "end_effect", "scope": "this_entry", "note": "The helm is destroyed."}]},
                                                     {"id": "other", "label": "2–20", "effects": [ref("dnd5e/magic-item/helm-of-brilliance", note="No effect.")]}]},
                                                 condition={"all": [WEAR, {"pred": "deals_damage_type", "args": {"type": "fire"}},
                                                                    {"pred": "failed_save_against_spell"}]}))]))
    E.append(MI("Helm of Comprehending Languages", [("^", "fx", act(cast("Comprehend Languages"), requires=WEAR))]))
    E.append(MI("Helm of Telepathy", [
        ("^", "fx", [{"op": "sense", "sense": "telepathy", "range_feet": 30, "when": WEAR},
                     act(cast("Detect Thoughts", dc=13), freq=DAWN, requires=WEAR),
                     act(cast("Suggestion", dc=13), freq=DAWN, requires=WEAR)])]))
    E.append(MI("Helm of Teleportation", [("^", "fx", [charges(3, "1d3"), act(cast("Teleport"), uses=1, requires=WEAR)])]))
    E.append(MI("Holy Avenger", [
        ("^", "fx", plus_weapon(3) + [trig("hits_with_attack_roll", dmg("2d10", "radiant", target=INHERIT),
                                           condition=hit_with_this(type_in("fiend", "undead")))]),
        ("While you hold the drawn weapon", "fx", adv("saving_throw", {"all": [HOLD, {"pred": "in_aura"}, {"pred": "save_against_spell_or_magic"}]},
                                                      target={"kind": "area", "area": {"shape": "emanation", "origin": "self", "moves_with_origin": True,
                                                                                       "size_feet": {"scale": {"by": "class_level.paladin", "steps": [
                                                                                           {"from": 0, "value": 10}, {"from": 17, "value": 30}]}}},
                                                              "filter": {"allies_only": True, "include_self": True}}))]))
    E.append(MI("Horn of Blasting", [
        ("^", "fx", act([save("con", 15, on_fail=[dmg("5d8", "thunder"), cond("deafened", mins(1))], half=True,
                              target=area("cone", 30, origin="self"), note="Audible to 600 feet; on a success, half damage only."),
                         dmg("10d8", "thunder", target={"kind": "object", "area": {"shape": "cone", "size_feet": 30, "origin": "self"},
                                                        "filter": {"objects": "not_worn_or_carried"}},
                             note="Glass or crystal objects in the Cone.")])),
        ("Each use of the horn’s magic", "fx", {"op": "choice", "id": "explode", "choose": 1, "note": "20 percent chance per use.", "options": [
            {"id": "explodes", "label": "Explodes (20%)", "effects": [dmg("10d6", "force", target=SELF), {"op": "end_effect", "scope": "this_entry",
                                                                                                         "note": "The horn is destroyed."}]},
            {"id": "safe", "label": "No explosion (80%)", "effects": [ref("dnd5e/magic-item/horn-of-blasting", note="No effect.")]}]})]))
    valhalla = item_nodes("Horn of Valhalla")
    E.append(MI("Horn of Valhalla", [
        ("^", "fx", act({"op": "summon", "creature": "dnd5e/creature/berserker", "count": {"var": "item_variant_spirits"},
                         "controller": "summoner", "duration": hours(1, ends_on=[{"event": "drops_to_0_hp"}]),
                         "note": "Warrior spirits from Ysgard within 60 feet; Immunity to Charmed and Frightened."})),
        ("^", "rule", {"id": "recharge_days", "days": 7}),
        ("Four types of *Horn of Valhalla*", "md", md("horn_type", "Which type of horn is this? (choose or roll 1d100)",
                                                      "The GM chooses the horn’s type or determines it randomly by rolling on the following table.")),
        ("If you blow the horn without", "rule", {"id": "requirement", "unmet": "spirits attack you", "met": "Friendly, follow your commands"}),
        ("| **1d100**", "table", tab("Horn of Valhalla", ["1d100", "Horn Type", "Spirits", "Requirement"], rows_of(valhalla)))],
        data={"item": {"variants": [{"variant": r[1], "spirits": int(r[2]), "requirement": r[3]} for r in rows_of(valhalla)]}}))
    E.append(horseshoes("Horseshoes of a Zephyr", [
        {"op": "modifier", "stat": "water_walk", "mode": "set", "value": 1, "note": "Floats 4 inches above any surface, including water or lava."},
        {"op": "modifier", "stat": "leaves_tracks", "mode": "set", "value": 0},
        {"op": "modifier", "stat": "ignores_difficult_terrain", "mode": "set", "value": 1},
        {"op": "reference", "rule": "dnd5e/condition/exhaustion", "note": "Up to 12 hours of travel a day without Exhaustion from extended travel."}]))
    E.append(horseshoes("Horseshoes of Speed", [speed("walk", 30, mode="add")]))
    E.append(MI("Immovable Rod", [
        ("^", "fx", act(ref("dnd5e/magic-item/immovable-rod", note="Fixed in place until the button is pushed again (Utilize action)."),
                        cost="action", action="dnd5e/action/utilize")),
        ("^", "rule", {"id": "hold", "max_lb": 8000, "overload": "deactivates and falls",
                       "move": {"action": "dnd5e/action/utilize", "check": "str.athletics", "dc": 30, "distance_feet": 10}})]))
    E.append(MI("Instant Fortress", [
        ("^", "fx", act(ref("dnd5e/magic-item/instant-fortress", note="Command word: the statuette grows into the tower; repeat to revert (only if empty)."))),
        ("^", "rule", {"id": "deploy", "statuette_inches": 1, "pushes_creatures_and_unattended_objects_out": True}),
        ("The tower is 20 feet on a side", "rule", {"id": "tower", "side_feet": 20, "height_feet": 30, "floors": 2,
                                                    "connector": ["ladder", "staircase", "ramp"], "roof_trapdoor": True,
                                                    "door": {"opens_on_command": "bonus_action", "immune": [SP("Knock")]}}),
        ("Magic prevents the tower", "rule", {"id": "durability", "cannot_tip": True,
                                              "parts": {"ac": 20, "hp": 100, "immune": ["bludgeoning", "piercing", "slashing"],
                                                        "except": "siege equipment", "resist": "all other"},
                                              "repair": {"only": SP("Wish"), "counts_as": "replicating a spell of level 8 or lower", "restores": "all"}})]))
    E.append(MI("Ioun Stone", [
        ("^", "desc", None),
        ("When you take a Magic action to toss", "rule", {"id": "orbit", "distance_feet": "1d3", "max_orbiting": 3}),
        ("Each *Ioun Stone* orbiting", "rule", {"id": "worn", "counts_as_worn": True, "avoids_attacks_and_snatching": True}),
        ("As a Utilize action, you can seize", "rule", {"id": "stow", "action": "dnd5e/action/utilize", "attunement_ends": "falls"}),
        ("The type of stone determines", "md", md("ioun_type", "Which type of Ioun Stone is this?", "The type of stone determines its rarity and effects.")),
        ioun("Absorption", trig({"event": "sees_creature_casting_spell", "which": "each"}, ref("dnd5e/magic-item/ioun-stone",
                                                                                              note="Cancel a spell of level 4 or lower; resources wasted; burns out after 20 levels."),
                                cost="reaction", optional=True, condition=ORBIT)),
        ioun("Agility", mod("ability_score.dex", 2, ORBIT, note="To a maximum of 20.")),
        ioun("Awareness", adv(["initiative", "ability_check"], {"all": [ORBIT, {"any": [{"pred": "roll_is", "args": {"roll": "initiative"}},
                                                                                      {"pred": "check_uses_skill", "args": {"skill": "perception"}}]}]})),
        ioun("Fortitude", mod("ability_score.con", 2, ORBIT, note="To a maximum of 20.")),
        ioun("Greater Absorption", trig({"event": "sees_creature_casting_spell", "which": "each"}, ref("dnd5e/magic-item/ioun-stone",
                                                                                                      note="Cancel a spell of level 8 or lower; burns out after 20 levels."),
                                        cost="reaction", optional=True, condition=ORBIT)),
        ioun("Insight", mod("ability_score.wis", 2, ORBIT, note="To a maximum of 20.")),
        ioun("Intellect", mod("ability_score.int", 2, ORBIT, note="To a maximum of 20.")),
        ioun("Leadership", mod("ability_score.cha", 2, ORBIT, note="To a maximum of 20.")),
        ioun("Mastery", mod("proficiency_bonus", 1, ORBIT)),
        ioun("Protection", mod("ac", 1, ORBIT)),
        ioun("Regeneration", trig({"event": "hour_elapsed", "which": "each"}, {"op": "heal", "amount": 15},
                                  condition={"all": [ORBIT, {"not": {"pred": "at_zero_hp"}}]})),
        ioun("Reserve", ref("dnd5e/magic-item/ioun-stone", note="Stores up to 4 levels of spells; found with 1d4 levels chosen by the GM.")),
        ("Any creature can cast a spell of level 1 through 4", "rule", {"id": "reserve_store", "spell_levels": [1, 4], "by_touch": True,
                                                                        "space": "slot level used", "overflow": "expended without effect"}),
        ("While this stone orbits your head, you can cast", "rule", {"id": "reserve_cast", "uses_original": ["slot_level", "spell_save_dc",
                                                                                                         "spell_attack_bonus", "spellcasting_ability"]}),
        ioun("Strength", mod("ability_score.str", 2, ORBIT, note="To a maximum of 20.")),
        ioun("Sustenance", {"op": "restrict", "restrictions": ["need_food_or_drink"], "when": ORBIT, "note": "You don't need to eat or drink."})]))
    E.append(MI("Iron Bands", [
        ("^", "rule", {"id": "sphere", "diameter_inches": 3, "weight_lb": 1}),
        ("^", "fx", act({"op": "attack", "attack_type": "ranged",
                         "bonus": {"op": "add", "args": [{"var": "ability_mod.dex"}, {"var": "proficiency_bonus"}]},
                         "target": creature(60, must_see=True, sizes=["tiny", "small", "medium", "large", "huge"]),
                         "on_hit": [cond("restrained", {"kind": "until_event", "until": {"event": "bonus_action_taken"}},
                                         note="Until you issue the release command as a Bonus Action.")]}, freq=DAWN)),
        ("A creature that can touch the bands", "fx", check("str", 20, skill="athletics",
                                                           on_success=[{"op": "remove_condition", "conditions": ["dnd5e/condition/restrained"]},
                                                                       {"op": "end_effect", "scope": "this_entry", "note": "The bands are destroyed."}],
                                                           on_fail=ref("dnd5e/magic-item/iron-bands", note="Further attempts by that creature fail for 24 hours."),
                                                           note="Takes an action.")),
        ("Once the bands are used", "sys", ["/effects/0"])]))
    E.append(MI("Iron Flask", [
        ("^", "fx", act(save("wis", 17, on_fail=ref("dnd5e/magic-item/iron-flask", note="Trapped in the flask until released."),
                             target=creature(60, must_see=True), note="Only if the flask is empty and the target is native to another plane; Advantage if trapped before."),
                        requires=HOLD)),
        ("^", "rule", {"id": "prison", "capacity": 1, "no_aging": True, "no_breath_food_drink": True}),
        ("You can take a Magic action to remove", "fx", act(ref("dnd5e/magic-item/iron-flask", duration=hours(1),
                                                                note="Released creature obeys your commands for 1 hour; defends itself against suicidal orders or none."))),
        ("An *Identify* spell reveals", "rule", {"id": "identify", "reveals_occupied": SP("Identify"), "type_only_by_opening": True}),
        ("An *Identify* spell reveals", "md", md("flask_occupant", "Does a newly found flask already contain a creature, and which?",
                                                 "A newly discovered *Iron Flask* might already contain a creature chosen by the GM."))]))
    E.append(MI("Javelin of Lightning", [
        ("^", "fx", trig("hits_with_attack_roll", ref("dnd5e/magic-item/javelin-of-lightning", note="Deal Lightning damage instead of Piercing."),
                         optional=True, condition={"pred": "attack_uses_weapon", "args": THIS})),
        ("***Lightning Bolt.***", "fx", act([save("dex", 13, on_fail=dmg("4d6", "lightning"), half=True,
                                                  target={"kind": "area", "area": {"shape": "line", "size_feet": 120, "width_feet": 5, "origin": "self"},
                                                          "filter": {"include_self": False}},
                                                  note="A Line between you and a target up to 120 feet away; the javelin reappears in your hand.")],
                                            cost="action", action="dnd5e/action/attack", freq=DAWN))]))
    E.append(MI("Lantern of Revealing", [
        ("^", "rule", {"id": "lantern", "burn_hours": 6, "fuel": "dnd5e/gear/oil", "bright_feet": 30, "dim_feet": 30,
                       "hood": {"action": "dnd5e/action/utilize", "dim_feet": 5}}),
        ("^", "fx", ref("dnd5e/condition/invisible", note="Invisible creatures and objects in the Bright Light are visible."))]))
    E.append(MI("Luck Blade", [
        ("^", "fx", plus_weapon(1) + [mod("saving_throw", 1, {"pred": "possesses_item", "args": THIS})]),
        ("***Luck.***", "fx", {"op": "activation", "cost": "none", "frequency": DAWN, "then": [{"op": "reroll", "rolls": ["d20_test"], "keep": "new",
                               "when": {"all": [{"pred": "possesses_item", "args": THIS}, {"pred": "roll_succeeded", "args": {"value": False}},
                                                {"not": {"pred": "has_condition", "args": {"condition": "incapacitated"}}}]},
                               "note": "No action required; one failed D20 Test."}]}),
        ("***Wish.***", "fx", [charges("1d3", note="Not regained; the property is lost with no charges."),
                               act(cast("Wish"), uses=1, freq=DAWN, requires=HOLD)])]))
    E.append(MI("Mace of Disruption", [
        ("^", "fx", trig("hits_with_attack_roll", [dmg("2d6", "radiant", target=INHERIT),
                                                   save("wis", 15, on_fail={"op": "end_effect", "scope": "this_entry_on_target", "note": "Destroyed."},
                                                        on_success=cond("frightened", until_turn("turn_end")), target=INHERIT,
                                                        when={"pred": "hp_at_most", "args": {"hp": 25}},
                                                        note="Only if it has 25 Hit Points or fewer after the damage.")],
                         condition=hit_with_this(type_in("fiend", "undead")))),
        ("***Light.***", "rule", {"id": "light", "bright_feet": 20, "dim_feet": 20, "while": "held"})]))
    E.append(MI("Mace of Smiting", [
        ("^", "fx", plus_weapon(1) + [mod("attack_roll", 2, {"all": [WIELD, type_in("construct")]}),
                                      mod("damage_roll", 2, {"all": [WIELD, type_in("construct")]})]),
        ("When you roll a 20", "fx", trig("rolls_natural_20_attack", {"op": "choice", "id": "construct", "choose": 1, "options": [
            {"id": "construct", "label": "Construct", "effects": [dmg(14, "bludgeoning", target=INHERIT),
                                                                  {"op": "end_effect", "scope": "this_entry_on_target", "when": {"pred": "hp_at_most", "args": {"hp": 25}},
                                                                   "note": "Destroyed if 25 Hit Points or fewer after the damage."}]},
            {"id": "other", "label": "Other", "effects": [dmg(7, "bludgeoning", target=INHERIT)]}]},
            condition={"pred": "attack_uses_weapon", "args": THIS}))]))
    E.append(MI("Mace of Terror", [
        ("^", "fx", [charges(3, "1d3"),
                     act(save("wis", 15, on_fail=cond("frightened", mins(1)), repeat=EACH_END,
                              target={"kind": "area", "area": {"shape": "emanation", "size_feet": 30, "origin": "self"}, "filter": {"predicate": {"pred": "chosen_by_source"}}}),
                         uses=1, requires=HOLD)]),
        ("Frightened in this way", "fx", [{"op": "restrict", "restrictions": ["make_opportunity_attacks", "actions_other_than_dash_or_escape"],
                                           "note": "Spends its turns moving as far away as it can; may Dodge if it can't move."}])]))
    E.append(MI("Mantle of Spell Resistance", [("^", "fx", adv("saving_throw", {"all": [WEAR, {"pred": "save_against_spell"}]}))]))
    E.append(manual("Manual of Bodily Health", "con"))
    E.append(manual("Manual of Gainful Exercise", "str"))
    golems = item_nodes("Manual of Golems")
    E.append(MI("Manual of Golems", [
        ("^", "md", md("golem_type", "Which golem does this manual make? (choose or roll 1d20)",
                       "The GM chooses the type or determines it randomly by rolling on the accompanying table.")),
        ("^", "rule", {"id": "prerequisite", "spellcaster": True, "min_level_5_slots": 2}),
        ("^", "fx", trig({"event": "reads_item"}, dmg("6d6", "psychic"), condition={"not": {"pred": "can_use_item", "args": THIS}})),
        ("To create a golem", "rule", {"id": "creation", "time": "table", "max_rest_hours_per_day": 8, "uninterrupted": True, "cost": "table"}),
        ("Once you finish creating", "fx", ref("dnd5e/rule/stat-block-overview", note="The golem of the manual's type (table) animates under your control; the book is consumed.")),
        ("| **1d20**", "table", tab("Manual of Golems", ["1d20", "Golem", "Time", "Cost"], rows_of(golems))),
        ("| **1d20**", "ref", ["dnd5e/creature/clay-golem", "dnd5e/creature/flesh-golem", "dnd5e/creature/iron-golem", "dnd5e/creature/stone-golem"])]))
    E.append(manual("Manual of Quickness of Action", "dex"))
    E.append(MI("Marvelous Pigments", [
        ("^", "rule", {"id": "box", "pots": "1d4", "weight_lb": 1}),
        ("Using the brush", "fx", act(ref("dnd5e/magic-item/marvelous-pigments", note="Paint objects and terrain within a 20-foot Cube; they become real."),
                                      cost="none", action=None, duration={"kind": "minutes", "amount": 10, "concentration": True},
                                      note="Remain in the Cube; broken Concentration or leaving wastes the pot.")),
        ("When the work is done", "rule", {"id": "real", "pit_within_cube": True}),
        ("No object created", "rule", {"id": "value", "max_object_gp": 25, "max_total_gp": 500, "excess": "worthless fakes"}),
        ("If you paint a form of energy", "rule", {"id": "energy", "dissipates_harmlessly": True})]))
    E.append(MI("Medallion of Thoughts", [("^", "fx", [charges(5, "1d4"), act(cast("Detect Thoughts", dc=13), uses=1, requires=WEAR)])]))
    E.append(MI("Mirror of Life Trapping", [
        ("^", "rule", {"id": "object", "height_feet": 4, "width_feet": 2, "weight_lb": 50, "ac": 11, "hp": 10,
                       "immunities": ["poison", "psychic"], "vulnerabilities": ["bludgeoning"], "destroyed_at_0_hp": True}),
        ("If the mirror is hanging", "fx", act(ref("dnd5e/magic-item/mirror-of-life-trapping", note="Command word toggles activation."),
                                               requires={"pred": "within_feet_of_item", "args": {"feet": 5, "item": "this"}})),
        ("Any creature other than you", "fx", trig({"event": "sees_reflection", "whose": "any", "which": "each"},
                                                   save("cha", 15, on_fail=ref("dnd5e/magic-item/mirror-of-life-trapping", note="Trapped in one of 12 cells with its gear."),
                                                        note="Advantage if it knows the mirror's nature; Constructs succeed automatically."),
                                                   condition={"all": [{"pred": "effect_active"}, {"pred": "within_feet_of_item", "args": {"feet": 30, "item": "this"}}]})),
        ("An extradimensional cell", "rule", {"id": "cell", "visibility_feet": 10, "no_aging_food_drink_sleep": True, "escape": "planar travel magic"}),
        ("If the mirror traps a creature", "rule", {"id": "overflow", "cells": 12, "full": "frees one at random", "shattered": "frees all"}),
        ("While within 5 feet of the mirror", "rule", {"id": "converse", "cost": "dnd5e/action/magic", "range_feet": 5}),
        ("In a similar way", "rule", {"id": "free", "cost": "dnd5e/action/magic", "second_command_word": True}),
        ("Placing the mirror", "rule", {"id": "extradimensional_conflict", "with": ["dnd5e/magic-item/bag-of-holding", "dnd5e/magic-item/portable-hole"],
                                        "both_destroyed": True, "gate": "astral_plane", "one_way": True}),
        ("Placing the mirror", "fx", {"op": "move", "mode": "teleport", "target": area("emanation", 10, origin="point"),
                                      "when": {"not": {"pred": "behind_cover", "args": {"cover": "total"}}},
                                      "note": "Creatures within 10 feet of the gate and not behind Total Cover go to a random location on the Astral Plane."})]))
    E.append(MI("Mithral Armor", [
        ("^", "rule", {"id": "mithral", "under_clothes": True}),
        ("^", "fx", [{"op": "modifier", "stat": "armor_stealth_disadvantage", "mode": "set", "value": 0, "when": WEAR},
                     {"op": "modifier", "stat": "armor_strength_requirement", "mode": "set", "value": 0, "when": WEAR}])]))
    deck = item_nodes("Mysterious Deck")
    cards = {
        "Balance": ref("dnd5e/magic-item/mysterious-deck", note="Optionally +2 to one ability (max 22) and −2 to another (not one at 5 or lower)."),
        "Comet": ref("dnd5e/magic-item/mysterious-deck", note="Choose a foe at your next Initiative; if you reduce it to 0 HP, Advantage on Death Saving Throws for 1 year."),
        "Donjon": ref("dnd5e/magic-item/mysterious-deck", note="Imprisoned in suspended animation; Artifacts stay; only Wish reveals the location; no more draws."),
        "Euryale": mod("saving_throw", -2, note="Curse; only a god or the Fates card ends it."),
        "Fates": ref("dnd5e/magic-item/mysterious-deck", note="Avoid or erase one event, any time before you die."),
        "Flames": ref("dnd5e/magic-item/mysterious-deck", note="A powerful devil becomes your enemy until one of you dies."),
        "Fool": adv("d20_test", mode="disadvantage", duration=hours(72), note="Also draw another card (not a declared draw)."),
        "Gem": ref("dnd5e/magic-item/mysterious-deck", note="25 jewelry pieces worth 2,000 GP each or 50 gems worth 1,000 GP each."),
        "Jester": {"op": "choice", "id": "jester", "choose": 1, "options": [
            {"id": "advantage", "label": "Advantage on D20 Tests for 72 hours", "effects": [adv("d20_test", duration=hours(72))]},
            {"id": "draws", "label": "Draw two additional cards", "effects": [ref("dnd5e/magic-item/mysterious-deck")]}]},
        "Key": ref("dnd5e/magic-item/mysterious-deck", note="A Rare or rarer magic weapon you're proficient with (GM's choice)."),
        "Knight": {"op": "summon", "creature": "dnd5e/creature/knight", "controller": "summoner", "note": "Within 30 feet; same alignment; loyal until death."},
        "Moon": ref("dnd5e/spell/wish", note="You can cast Wish 1d3 times."),
        "Puzzle": mod("ability_score", {"op": "neg", "args": [{"op": "add", "args": ["1d4", 1]}]},
                      note="Intelligence or Wisdom (minimum 1); draw one additional card."),
        "Rogue": ref("dnd5e/magic-item/mysterious-deck", note="An unknown NPC becomes Hostile; only Wish or divine intervention ends it."),
        "Ruin": ref("dnd5e/magic-item/mysterious-deck", note="All non-magic-item wealth you carry or own is lost."),
        "Sage": ref("dnd5e/magic-item/mysterious-deck", note="Within one year, one question answered truthfully."),
        "Skull": {"op": "summon", "creature": "dnd5e/creature/avatar-of-death", "controller": "none",
                  "note": "Targets only you; an ally who damages it summons another; slain creatures can't be restored to life."},
        "Star": mod("ability_score", 2, note="One ability of your choice, to a maximum of 24."),
        "Sun": trig({"event": "dawn", "which": "each"}, {"op": "temp_hp", "amount": 10}, note="Also a magic item chosen by the GM appears on your person."),
        "Talons": ref("dnd5e/magic-item/mysterious-deck", note="Every magic item you wear or carry disintegrates; Artifacts vanish."),
        "Throne": {"op": "proficiency", "category": "skill", "choose": 1, "from": ["history", "insight", "intimidation", "persuasion"],
                   "expertise": True, "note": "Also a monster-held keep."},
        "Void": ref("dnd5e/magic-item/mysterious-deck", note="Soul trapped in an object guarded somewhere; Wish only reveals the location; no more draws."),
    }
    card_md = {"Key": "The GM chooses the weapon.", "Knight": "The GM can use a different stat block to represent the knight, as desired.",
               "Rogue": "An NPC of the GM’s choice becomes Hostile toward you.", "Sun": "A magic item (chosen by the GM) appears on your person.",
               "Void": "Your soul is drawn from your body and contained in an object in a place of the GM’s choice."}
    card_items = []
    for name, fx in cards.items():
        card_items.append((f"***{name}.***", "fx", fx))
        if name in card_md:
            card_items.append((f"***{name}.***", "md", md(f"card_{name.lower()}", f"{name} card: the GM's choice.", card_md[name])))
    E.append(MI("Mysterious Deck", [
        ("^", "rule", {"id": "deck", "cards": {"13": 75, "22": 25}, "unit": "percent"}),
        ("Before you draw a card", "rule", {"id": "draws", "declare_count": True, "excess_no_effect": True, "max_interval_hours": 1,
                                            "undrawn_fly_out": True}),
        ("Once a card is drawn", "rule", {"id": "reappear", "except": ["Fool", "Jester"], "reroll_if_gone": True}),
        ("##### Mysterious Deck", "table", tab("Mysterious Deck", ["1d100 (13-Card Deck)", "1d100 (22-Card Deck)", "Card"],
                                               [r for r in rows_of(deck) if len(r) == 3 and not r[0].startswith("(") and r[0] != "Deck)"])),
        ("Each card’s effect is described below.", "desc", None)] + card_items))
    E.append(creature_entry("Avatar of Death", 232, LOT, "Magic Items/Magic Items A–Z/Mysterious Deck/Avatar of Death"))
    E.append(MI("Necklace of Adaptation", [
        ("^", "fx", [{"op": "modifier", "stat": "breathe_any_environment", "mode": "set", "value": 1, "when": WEAR},
                     adv("saving_throw", {"all": [WEAR, {"pred": "save_against_condition", "args": {"condition": "poisoned"}}]})])]))
    E.append(MI("Necklace of Fireballs", [
        ("^", "rule", {"id": "beads", "count": "1d6 + 3"}),
        ("^", "fx", act(cast("Fireball", level=3, dc=15, note="Thrown up to 60 feet."))),
        ("You can hurl multiple beads", "rule", {"id": "multiple", "extra_damage_per_bead_after_first": "1d6", "max_damage": "12d6"})]))
    beads = item_nodes("Necklace of Prayer Beads")
    E.append(MI("Necklace of Prayer Beads", [
        ("^", "rule", {"id": "beads", "magic": "1d4 + 2", "removed_bead_loses_magic": True}),
        ("Six types of magic beads", "md", md("bead_types", "Which type is each magic bead? (choose or roll 1d20 each)",
                                              "The GM decides the type of each bead on the necklace or determines it randomly by rolling on the table below.")),
        ("Six types of magic beads", "fx", [act(cast(s, level=l, dc={"var": "spell_save_dc"}), cost="bonus_action", freq=DAWN, requires=WEAR,
                                                name=b) for b, s, l in (("Bead of Blessing", "Bless", None), ("Bead of Curing", "Cure Wounds", 2),
                                                                         ("Bead of Favor", "Greater Restoration", None), ("Bead of Smiting", "Shining Smite", None),
                                                                         ("Bead of Summons", "Guardian of Faith", None), ("Bead of Wind Walking", "Wind Walk", None))]),
        ("| **1d20**", "table", tab("Necklace of Prayer Beads", ["1d20", "Bead", "Spell"], rows_of(beads)))]))
    E.append(MI("Nine Lives Stealer", [
        ("^", "fx", plus_weapon(2)),
        ("***Life Stealing.***", "fx", [charges("1d8 + 1", note="Not regained; the property is lost with no charges."),
                                        trig("rolls_natural_20_attack", save("con", 15, on_fail=[DIES, {"op": "spend", "resource": "charges", "amount": 1}],
                                                                             target=INHERIT, note="Constructs and Undead succeed automatically."),
                                             condition={"all": [{"pred": "attack_uses_weapon", "args": THIS}, {"pred": "hp_below", "args": {"hp": 100}},
                                                                {"pred": "resource_available", "args": {"resource": "charges"}}]})])]))
    return E


if __name__ == "__main__":
    extend_registries(REGISTRY, LOT)
    out = entries()
    for e in out:
        write_entry(e)
    print(f"wrote {len(out)} entries")
