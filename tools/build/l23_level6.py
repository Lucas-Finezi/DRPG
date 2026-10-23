#!/usr/bin/env python3
"""L23 — Level 6 spells (31).

Usage: python3 -I tools/build/l23_level6.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (C, DC, EACH_END, INHERIT, MAGIC, MOD, SELF, SLOT, SP, STUDY, S_for, active,  # noqa: E402
                      all_but, area, attack, cond, creatures, dmg, extra_targets, heal, light, md, ref, save, touch,
                      until_turn, up, updice, write_all)

LOT = "L23"
S = S_for(LOT)
HL = "***Using a Higher-Level Spell Slot.***"
PLANAR = ["aberration", "celestial", "elemental", "fey", "fiend", "undead"]
M = lambda s: f"dnd5e/creature/{s}"  # noqa: E731


def entries():
    E = []
    E.append(S("Blade Barrier", [
        ("^", "rule", {"id": "wall", "shapes": [{"length_feet": 100, "height_feet": 20, "thickness_feet": 5},
                                                {"ring_diameter_feet": 60, "height_feet": 20, "thickness_feet": 5}],
                       "cover": "three_quarters", "difficult_terrain": True, "rule": "dnd5e/rule/cover"}),
        ("Any creature in the wall’s space", "fx", [
            save("dex", dmg("6d10", "force"), half=True, target={"kind": "area", "area": {"shape": "line", "size_feet": 100, "origin": "point"}, "range": "@range"}),
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "duration": "@duration", "then": [save("dex", dmg("6d10", "force"), half=True, target=INHERIT)]}])]))
    E.append(S("Chain Lightning", [
        ("^", "fx", save("dex", dmg("10d8", "lightning"), half=True,
                         target={"kind": "creature_or_object", "range": "@range", "must_see": True, "distinct": True,
                                 "count": {"op": "add", "args": [1, up(3, 6)]}},
                         note="The first target plus up to three others within 30 feet of it; each targeted by one bolt only.")),
        (HL, "sys", ["/effects/0/target/count"])]))
    E.append(S("Circle of Death", [
        ("^", "fx", save("con", dmg(updice(8, 8, 6, 2), "necrotic"), half=True, target=area("sphere", 60))),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    fey_attack = attack("melee_spell", [dmg({"op": "add", "args": [updice(3, 12, 6), MOD]}, "psychic"),
                                        cond("frightened", until_turn("turn_start", "source"),
                                             note="Both you and the spirit are the source of the fear.")])
    E.append(S("Conjure Fey", [
        ("^", "rule", {"id": "spirit", "size": "medium", "looks_like": "fey_creature_of_choice"}),
        ("^", "fx", fey_attack),
        ("As a Bonus Action on your later turns", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "move", "mode": "teleport", "distance_feet": 30, "note": "The spirit."}, fey_attack]}),
        (HL, "sys", ["/effects/0/on_hit/0/amount", "/effects/1/then/1/on_hit/0/amount"])]))
    E.append(S("Contingency", [
        ("^", "rule", {"id": "contingent_spell", "max_level": 5, "casting_time": "action", "can_target_you": True,
                       "both_slots_expended": True}),
        ("^", "md", md("contingency_trigger", "Has the described trigger occurred?",
                       "Instead, it takes effect when a certain trigger occurs. You describe that trigger when you cast the two spells.")),
        ("The contingent spell takes effect immediately", "rule", {"id": "release", "first_trigger": True, "involuntary": True,
                                                                    "then": "contingency_ends"}),
        ("The contingent spell takes effect only on you", "rule", {"id": "limits", "only_on_you": True, "one_at_a_time": True,
                                                                   "ends_if_material_not_on_person": True})]))
    E.append(S("Create Undead", [
        ("^", "fx", {"op": "repeat", "times": 3, "then": [{"op": "summon", "creature": M("ghoul"), "controller": "summoner", "initiative": "own"}],
                     "note": "Only at night; up to three corpses of Medium or Small Humanoids."}),
        ("As a Bonus Action on each of your turns", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            ref(SP("create-undead"), note="Command any or all of your creatures within 120 feet.")]}),
        ("As a Bonus Action on each of your turns", "rule", {"id": "no_command", "default": "dnd5e/action/dodge"}),
        ("The creature is under your control for 24 hours", "rule", {"id": "control", "hours": 24, "recast_reasserts": 3}),
        (HL, "rule", {"id": "upcast", "options_by_slot": {
            "7": [{M("ghoul"): 4}], "8": [{M("ghoul"): 5}, {M("ghast"): 2}, {M("wight"): 2}],
            "9": [{M("ghoul"): 6}, {M("ghast"): 3}, {M("wight"): 3}, {M("mummy"): 2}]}})]))
    E.append(S("Disintegrate", [
        ("^", "rule", {"id": "targets", "creature_nonmagical_object_or_force_creation": True, "example": SP("wall-of-force")}),
        ("A creature targeted by this spell", "fx", save("dex", dmg({"op": "add", "args": [updice(10, 6, 6, 3), 40]}, "force"),
                                                          target=creatures(must_see=True))),
        ("A creature targeted by this spell", "rule", {"id": "dust", "at_0_hp": "disintegrated_with_nonmagical_gear",
                                                       "revived_only_by": [SP("true-resurrection"), SP("wish")]}),
        ("This spell automatically disintegrates", "rule", {"id": "objects", "large_or_smaller": "disintegrated",
                                                            "huge_or_larger": "10_foot_cube_portion"}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Eyebite", [
        ("^", "fx", save("wis", {"op": "choice", "id": "eyebite", "choose": 1, "options": [
            {"id": "asleep", "label": "Asleep", "effects": [cond("unconscious", note="Wakes if it takes damage or is shaken awake with an action.")]},
            {"id": "panicked", "label": "Panicked", "effects": [cond("frightened", note="Must Dash away by the safest, shortest route; ends if 60+ feet away where it can't see you.")]},
            {"id": "sickened", "label": "Sickened", "effects": [cond("poisoned")]}]},
            target={"kind": "creature", "range": {"kind": "distance", "feet": 60}, "must_see": True})),
        ("On each of your turns until the spell ends", "fx", {"op": "activation", **MAGIC, "then": [
            ref(SP("eyebite"), note="Target another creature; not one that succeeded on a save against this casting.")]}),
        ("***Asleep.***", "sys", ["/effects/0/on_fail/0/options/0"]),
        ("***Panicked.***", "sys", ["/effects/0/on_fail/0/options/1"]),
        ("***Sickened.***", "sys", ["/effects/0/on_fail/0/options/2"])]))
    E.append(S("Find the Path", [
        ("^", "rule", {"id": "path", "familiar_location": True,
                       "fails_on": ["other_plane", "moving_destination", "unspecific_destination"]}),
        ("For the duration, as long as you are", "fx", {"op": "sense", "sense": "know_route", "range_feet": 0, "duration": "@duration",
                                                        "note": "Distance, direction and the most direct path at each choice, on the same plane."})]))
    E.append(S("Flesh to Stone", [
        ("^", "fx", save("con", cond("restrained"), target=creatures(must_see=True),
                         on_success={"op": "speed", "movement": "walk", "mode": "set", "value": 0, "duration": until_turn("turn_start", "source")},
                         note="Constructs automatically succeed.")),
        ("A Restrained target makes another", "fx", {"op": "trigger", "event": {"event": "turn_end", "whose": "target", "which": "each"},
                                                     "duration": "@duration",
                                                     "condition": {"pred": "has_condition", "args": {"condition": "restrained"}},
                                                     "then": [save("con", None, target=INHERIT,
                                                                   note="Three successes end the spell; three failures: Petrified for the duration (not necessarily consecutive).")]}),
        ("If you maintain your Concentration", "rule", {"id": "permanent", "full_duration": "petrified_until_greater_restoration",
                                                        "ended_by": SP("greater-restoration")})]))
    E.append(S("Forbiddance", [
        ("^", "rule", {"id": "ward", "floor_square_feet": 40000, "height_feet": 30, "blocks": ["teleportation", "portals", "planar_travel"],
                       "examples": [SP("gate"), SP("plane-shift")]}),
        ("In addition, the spell damages types", "fx", {
            "op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
            "duration": "@duration", "condition": {"pred": "creature_type_chosen"},
            "then": [dmg("5d10", ["radiant", "necrotic"], target=INHERIT, note="Type chosen when casting.")]}),
        ("In addition, the spell damages types", "rule", {"id": "types", "choose_any_of": PLANAR}),
        ("You can designate a password", "rule", {"id": "password", "speaker_takes_no_damage": True}),
        ("The spell’s area can’t overlap", "rule", {"id": "limits", "no_overlap": True, "daily_castings": 30, "then": "until_dispelled"})]))
    E.append(S("Freezing Sphere", [
        ("^", "fx", save("con", dmg(updice(10, 6, 6), "cold"), half=True, target=area("sphere", 60))),
        ("If the globe strikes a body of water", "rule", {"id": "water", "freeze_depth_inches": 6, "area_square_feet": 30, "ice_minutes": 1,
                                                          "swimmers_restrained": True,
                                                          "break_free": {"action": True, "check": {"ability": "str", "skill": "athletics", "dc": "spell_save_dc"}}}),
        ("You can refrain from firing", "rule", {"id": "delayed_globe", "throw_range_feet": 40, "sling_range": "normal",
                                                 "explodes_after_minutes": 1}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Globe of Invulnerability", [
        ("^", "rule", {"id": "barrier", "area": {"shape": "emanation", "size_feet": 10}, "immobile": True}),
        ("Any spell of level 5 or lower", "rule", {"id": "blocks", "spells_from_outside_level_at_most": up(5, 6)}),
        (HL, "sys", ["rule:blocks"])]))
    E.append(S("Guards and Wards", [
        ("^", "rule", {"id": "area", "floor_square_feet": 2500, "height_feet": 20,
                       "shapes": ["one_50_foot_square", "100_contiguous_5_foot_squares", "25_contiguous_10_foot_squares"]}),
        ("When you cast this spell, you can specify", "rule", {"id": "exemptions", "individuals": True, "password_range_feet": 5}),
        ("The spell creates the effects below", "rule", {"id": "dispelling", "dispel_magic_on_spell": False, "effects_dispellable": True,
                                                         "ends_when_all_four_dispelled": True, "daily_castings": 365}),
        ("***Corridors.***", "rule", {"id": "corridors", "heavily_obscured": True, "wrong_direction_percent": 50}),
        ("***Doors.***", "rule", {"id": "doors", "locked_as": SP("arcane-lock"), "disguised_doors": 10}),
        ("***Stairs.***", "rule", {"id": "stairs", "webs_as": SP("web"), "regrow_minutes": 10}),
        ("***Other Spell Effect.***", "rule", {"id": "other", "choose_one": [
            {"spell": SP("dancing-lights"), "corridors": 4}, {"spell": SP("magic-mouth"), "locations": 2},
            {"spell": SP("stinking-cloud"), "locations": 2}, {"spell": SP("gust-of-wind"), "corridor_or_room": 1},
            {"spell": SP("suggestion"), "square_feet": 5}]})]))
    E.append(S("Harm", [("^", "fx", save("con", [dmg("14d6", "necrotic"),
                                                 {"op": "modifier", "stat": "hp_max", "mode": "add",
                                                  "value": {"op": "neg", "args": [{"var": "damage_amount"}]},
                                                  "note": "Can't reduce the Hit Point maximum below 1."}],
                                         target=creatures(must_see=True),
                                         on_success=dmg({"op": "div", "args": ["14d6", 2]}, "necrotic", note="Half damage only.")))]))
    E.append(S("Heal", [
        ("^", "fx", [heal(up(70, 6, 10), target=creatures(must_see=True)),
                     {"op": "remove_condition", "conditions": [C("blinded"), C("deafened"), C("poisoned")], "target": INHERIT}]),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Heroes’ Feast", [
        ("^", "rule", {"id": "feast", "cube_feet": 10, "consume_hours": 1, "max_creatures": 12}),
        ("A creature that partakes", "fx", [
            {"op": "defense", "kind": "resistance", "damage_types": ["poison"], "duration": {"kind": "hours", "amount": 24}},
            {"op": "defense", "kind": "immunity", "conditions": [C("frightened"), C("poisoned")], "duration": {"kind": "hours", "amount": 24}},
            {"op": "modifier", "stat": "hp_max", "mode": "add", "value": {"var": "rolled.hit_point_bonus"}, "duration": {"kind": "hours", "amount": 24},
             "note": "2d10, rolled once; the creature gains the same number of Hit Points."},
            heal({"var": "rolled.hit_point_bonus"})])]))
    E.append(S("Instant Summons", [
        ("^", "rule", {"id": "mark", "object_max_lb": 10, "object_max_feet": 6, "different_sapphire_each_casting": True}),
        ("Thereafter, you can take a Magic action", "fx", {"op": "activation", **MAGIC, "then": [
            ref(SP("instant-summons"), note="Crush the sapphire: the object appears in your hand regardless of distance or plane; the spell ends.")]}),
        ("If another creature is holding", "rule", {"id": "held", "not_transported": True, "learn_holder_and_location": True})]))
    E.append(S("Irresistible Dance", [
        ("^", "fx", save("wis", [cond("charmed"),
                                 {"op": "roll_mode", "mode": "disadvantage", "rolls": ["saving_throw.dex", "attack_roll"], "duration": "@duration"},
                                 {"op": "roll_mode", "mode": "advantage", "rolls": ["attack_roll"], "direction": "against", "duration": "@duration"},
                                 {"op": "activation", "cost": "action", "then": [save("wis", None, target=INHERIT,
                                                                                     on_success={"op": "end_effect", "scope": "this_entry_on_target"})],
                                  "note": "The target collects itself and repeats the save."}],
                         target=creatures(must_see=True),
                         on_success={"op": "restrict", "restrictions": ["move"], "duration": until_turn("turn_end", "target"),
                                     "note": "Dances in place, spending all its movement."})),
        ("On a failed save", "rule", {"id": "dance", "spends_all_movement_dancing": True})]))
    E.append(S("Magic Jar", [
        ("^", "rule", {"id": "jar", "body_catatonic": True, "aware_from_container": True, "can_move": False, "can_react": False,
                       "only_action": "project_soul_100_feet"}),
        ("You can attempt to possess", "fx", save("cha", ref(SP("magic-jar"), note="Your soul enters the target's body; its soul is trapped in the container."),
                                                  target=creatures(must_see=True, creature_types=["humanoid"]),
                                                  note="Not creatures warded by Protection from Evil and Good or Magic Circle; on a success, immune for 24 hours.")),
        ("Once you possess a creature’s body", "rule", {"id": "possession", "replaced_by_host": ["hp", "hit_point_dice", "str", "dex", "con", "speed", "senses"],
                                                        "keep_other_statistics": True}),
        ("Meanwhile, the possessed creature’s soul", "rule", {"id": "host_soul", "perceives_from_container": True, "can_move": False,
                                                              "condition": C("incapacitated")}),
        ("While possessing a body", "fx", {"op": "activation", **MAGIC, "then": [
            ref(SP("magic-jar"), note="Return to the container if within 100 feet.")]}),
        ("While possessing a body", "rule", {"id": "host_dies", "save": {"ability": "cha", "dc": "spell_save_dc"},
                                             "success": "return_to_container_within_100_feet", "failure": "you_die"}),
        ("If the container is destroyed", "rule", {"id": "end", "soul_returns": True, "body_far_or_dead": "you_die",
                                                   "other_soul_in_container": "returns_if_body_alive_within_100_feet_else_dies"}),
        ("When the spell ends, the container", "rule", {"id": "container", "destroyed_on_end": True})]))
    E.append(S("Mass Suggestion", [
        ("^", "rule", {"id": "suggestion", "max_words": 25, "max_targets": 12, "must_sound_achievable": True, "no_obvious_harm": True}),
        ("Each target must succeed", "fx", save("wis", cond("charmed", note="Ends if you or your allies damage it; ends when the activity is completed."),
                                                target=creatures(12, must_see=True))),
        (HL, "rule", {"id": "upcast_duration_days", "by_slot_level": {"7": 10, "8": 30, "9": 366}})]))
    E.append(S("Move Earth", [
        ("^", "rule", {"id": "reshape", "area_max_feet": 40, "materials": ["dirt", "sand", "clay"], "max_change": "half_largest_dimension",
                       "minutes_to_complete": 10, "creatures_trapped_or_injured": False}),
        ("At the end of every 10 minutes", "rule", {"id": "new_area", "every_minutes": 10}),
        ("This spell can’t manipulate natural stone", "md", md("collapse", "Does a structure made unstable by the new terrain collapse?",
                                                               "If the way you shape the terrain would make a structure unstable, it might collapse.")),
        ("Similarly, this spell doesn’t directly affect plant growth", "rule", {"id": "plants", "carried_along": True})]))
    E.append(S("Planar Ally", [
        ("^", "md", md("planar_ally_creature", "Which creature does the entity send?",
                       "If you know a specific creature’s name, you can speak that name when you cast this spell to request that creature, though you might get a different creature anyway (GM’s choice).")),
        ("^", "rule", {"id": "ally", "creature_types": ["celestial", "elemental", "fiend"]}),
        ("When the creature appears", "md", md("bargain", "Does the creature accept the service and at what price?",
                                               "When the creature appears, it is under no compulsion to behave a particular way. You can ask it to perform a service in exchange for payment, but it isn’t obliged to do so.",
                                               reason="narrative")),
        ("Payment can take a variety of forms", "desc", None),
        ("A task that can be measured in minutes", "rule", {"id": "payment_gp", "per_minute": 100, "per_hour": 1000, "per_day": 10000,
                                                            "max_days": 10, "gm_may_adjust": True}),
        ("After the creature completes the task", "rule", {"id": "return", "returns_home_after_task": True, "no_agreement": "returns_immediately"})]))
    E.append(S("Programmed Illusion", [
        ("^", "rule", {"id": "illusion", "max_cube_feet": 30, "script_max_minutes": 5, "imperceptible_until_triggered": True}),
        ("When the trigger you specify occurs", "rule", {"id": "repeat", "dormant_minutes_between": 10}),
        ("The trigger can be as general", "md", md("illusion_trigger", "Does the specified trigger occur?",
                                                   "The trigger can be as general or as detailed as you like, though it must be based on visual or audible phenomena that occur within 30 feet of the area.")),
        ("Physical interaction with the image", "fx", STUDY)]))
    E.append(S("Sunbeam", [
        ("^", "fx", save("con", [dmg("6d8", "radiant"), cond("blinded", until_turn("turn_start", "source"))],
                         target=area("line", 60, "self"), on_success=dmg({"op": "div", "args": ["6d8", 2]}, "radiant"))),
        ("Until the spell ends, you can take a Magic action", "fx", {"op": "activation", **MAGIC, "then": [ref(SP("sunbeam"), note="A new Line.")]}),
        ("For the duration, a mote", "rule", {"id": "light", "light": light(30, 30), "sunlight": True})]))
    E.append(S("Transport via Plants", [("^", "rule", {"id": "link", "source_plant_min_size": "large", "same_plane": True,
                                                       "destination_seen_or_touched": True, "movement_cost_feet": 5})]))
    E.append(S("True Seeing", [("^", "fx", {"op": "sense", "sense": "truesight", "range_feet": 120, "target": touch(willing=True),
                                            "duration": "@duration"})]))
    E.append(S("Wall of Ice", [
        ("^", "rule", {"id": "wall", "shapes": [{"dome_or_globe_radius_feet": 10}, {"panels": 10, "panel_feet": [10, 10]}],
                       "thickness_feet": 1}),
        ("If the wall cuts through a creature’s space", "fx", save("dex", dmg(updice(10, 6, 6, 2), "cold"), half=True,
                                                                    target={"kind": "creature"}, note="Pushed to the side you choose.")),
        ("The wall is an object", "rule", {"id": "durability", "ac": 12, "hp_per_10_foot_section": 30,
                                           "immunities": ["cold", "poison", "psychic"], "vulnerabilities": ["fire"],
                                           "destroyed_leaves": "frigid_air"}),
        ("A creature moving through the sheet", "fx", {"op": "trigger", "event": {"event": "moves_within_area"},
                                                       "frequency": {"count": 1, "per": "turn"},
                                                       "then": [save("con", dmg(updice(5, 6, 6), "cold"), half=True, target=INHERIT)]}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Wall of Thorns", [
        ("^", "rule", {"id": "wall", "shapes": [{"length_feet": 60, "height_feet": 10, "thickness_feet": 5},
                                                {"circle_diameter_feet": 20, "height_feet": 20, "thickness_feet": 5}],
                       "blocks_line_of_sight": True}),
        ("When the wall appears", "fx", save("dex", dmg(updice(7, 8, 6), "piercing"), half=True,
                                             target={"kind": "area", "area": {"shape": "line", "size_feet": 60, "origin": "point"}, "range": "@range"})),
        ("A creature can move through the wall", "fx", {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"},
                                                        "frequency": {"count": 1, "per": "turn"}, "duration": "@duration",
                                                        "then": [save("dex", dmg(updice(7, 8, 6), "slashing"), half=True, target=INHERIT)]}),
        ("A creature can move through the wall", "rule", {"id": "movement", "movement_cost_multiplier": 4}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Wind Walk", [
        ("^", "fx", [{"op": "speed", "movement": "fly", "mode": "set", "value": 300, "hover": True,
                      "target": creatures(11, willing=True), "duration": "@duration", "note": "You and up to ten willing creatures."},
                     {"op": "defense", "kind": "immunity", "conditions": [C("prone")], "duration": "@duration"},
                     {"op": "defense", "kind": "resistance", "damage_types": ["bludgeoning", "piercing", "slashing"], "duration": "@duration"},
                     {"op": "restrict", "restrictions": ["actions_other_than_dash_or_magic"], "duration": "@duration"}]),
        ("^", "rule", {"id": "revert", "cost": "dnd5e/action/magic", "minutes": 1, "condition_while_reverting": C("stunned"),
                       "return_to_cloud": "magic_action_plus_1_minute"}),
        ("If a target is in cloud form", "rule", {"id": "descent", "feet_per_round": 60, "minutes": 1, "then": "falls_remaining_distance"})]))
    E.append(S("Word of Recall", [
        ("^", "fx", {"op": "move", "mode": "teleport", "target": creatures(6, willing=True),
                     "note": "You and up to five willing creatures within 5 feet to your designated sanctuary; no effect without one."}),
        ("You must designate a location", "rule", {"id": "sanctuary", "designated_by_casting_there": True})]))
    return E


REGISTRY = {
    "senses": [{"id": "know_route", "description": "Know the distance, direction and most direct path to a named destination.", "pages": [132]}],
    "restrictions": [{"id": "actions_other_than_dash_or_magic", "description": "The creature can take only the Dash action or a Magic action.", "pages": [173]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
