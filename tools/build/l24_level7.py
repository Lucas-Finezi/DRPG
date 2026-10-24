#!/usr/bin/env python3
"""L24 — Level 7 spells (20).

Usage: python3 -I tools/build/l24_level7.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (C, DC, EACH_END, INHERIT, MAGIC, MOD, SELF, SLOT, SP, STUDY, S_for, active,  # noqa: E402
                      all_but, area, attack, cond, creatures, dmg, extra_targets, heal, light, md, ref, save, tab, touch,
                      until_turn, up, updice, write_all)

LOT = "L24"
S = S_for(LOT)
HL = "***Using a Higher-Level Spell Slot.***"
PLANAR = ["aberration", "celestial", "elemental", "fey", "fiend", "undead"]


def entries():
    E = []
    sword = attack("melee_spell", dmg({"op": "add", "args": ["4d12", MOD]}, "force"))
    E.append(S("Arcane Sword", [
        ("^", "rule", {"id": "sword", "hovers_within_range": True}),
        ("When the sword appears", "fx", sword),
        ("On your later turns, you can take a Bonus Action", "fx", {"op": "activation", "cost": "bonus_action", "then": [
            {"op": "move", "mode": "move", "distance_feet": 30, "note": "The sword, to a spot you can see."}, sword]})]))
    lights = {"op": "choice", "id": "light", "choose": 1, "options": [
        {"id": "healing", "label": "Healing Light", "effects": [heal({"op": "add", "args": [updice(4, 12, 7), MOD]})]},
        {"id": "searing", "label": "Searing Light", "effects": [save("dex", dmg(updice(6, 12, 7), "radiant"), half=True, target=INHERIT)]}]}
    E.append(S("Conjure Celestial", [
        ("^", "fx", {**lights, "target": area("cylinder", 10),
                     "note": "Each creature you can see in the Cylinder; once per turn per creature."}),
        ("^", "rule", {"id": "pillar", "radius_feet": 10, "height_feet": 40}),
        ("**Healing Light.**", "sys", ["/effects/0/options/0"]),
        ("**Searing Light.**", "sys", ["/effects/0/options/1"]),
        ("Until the spell ends, Bright Light fills", "fx", {"op": "trigger", "event": {"event": "moves_on_turn"}, "duration": "@duration",
                                                            "then": [{"op": "move", "mode": "move", "distance_feet": 30, "note": "The Cylinder."}]}),
        ("Until the spell ends, Bright Light fills", "rule", {"id": "light", "bright_light_in_cylinder": True, "rule": "dnd5e/rule/bright-light"}),
        ("Whenever the Cylinder moves into", "fx", {"op": "trigger", "event": {"event": "creature_within_feet_of_effect"}, "optional": True,
                                                    "frequency": {"count": 1, "per": "turn"}, "duration": "@duration",
                                                    "then": [lights]}),
        (HL, "sys", ["/effects/0/options/0/effects/0/amount", "/effects/0/options/1/effects/0/on_fail/0/amount"])]))
    E.append(S("Delayed Blast Fireball", [
        ("^", "fx", {"op": "trigger", "event": {"event": "effect_ends"}, "then": [
            save("dex", dmg({"op": "add", "args": [updice(12, 6, 7), {"dice": {"count": {"var": "rounds_elapsed"}, "faces": 6}}]}, "fire"),
                 half=True, target=area("sphere", 20))],
            "note": "The bead explodes when the spell ends."}),
        ("The spell’s base damage is 12d6", "rule", {"id": "accumulation", "base": "12d6", "per_turn_end": "1d6"}),
        ("If a creature touches the glowing bead", "fx", {"op": "trigger", "event": {"event": "touches_effect"}, "then": [
            save("dex", {"op": "end_effect", "scope": "this_entry"}, target=INHERIT,
                 on_success={"op": "move", "mode": "move", "distance_feet": 40, "note": "It can throw the bead; it explodes on hitting a creature's space or a solid object."})]}),
        ("When the bead explodes, flammable objects", "ref", ["dnd5e/hazard/burning"]),
        (HL, "sys", ["/effects/0/then/0/on_fail/0/amount"])]))
    E.append(S("Divine Word", [
        ("^", "fx", save("cha", [
            {"op": "choice", "id": "by_hit_points", "choose": 1, "chooser": "gm", "note": "By the target's current Hit Points (50 or fewer).",
             "options": [{"id": "dies", "label": "0–20", "effects": [{"op": "modifier", "stat": "hp", "mode": "set", "value": 0, "note": "The target dies."}]},
                         {"id": "21_30", "label": "21–30", "effects": [cond(c, {"kind": "hours", "amount": 1}) for c in ("blinded", "deafened", "stunned")]},
                         {"id": "31_40", "label": "31–40", "effects": [cond(c, {"kind": "minutes", "amount": 10}) for c in ("blinded", "deafened")]},
                         {"id": "41_50", "label": "41–50", "effects": [cond("deafened", {"kind": "minutes", "amount": 1})]}]},
            ref(SP("divine-word"), when={"pred": "creature_type_in", "args": {"types": ["celestial", "elemental", "fey", "fiend"]}},
                note="Forced back to its plane of origin; can't return for 24 hours short of a Wish spell.")],
            target={"kind": "creature", "range": "@range"})),
        ("##### Divine Word Effects", "table", tab("Divine Word Effects", ["Hit Points", "Effect"]))]))
    E.append(S("Etherealness", [
        ("^", "rule", {"id": "border_ethereal", "vertical_movement_cost_multiplier": 2, "perceive_origin_plane_within_feet": 60}),
        ("While on the Ethereal Plane", "rule", {"id": "interaction", "only_ethereal": True}),
        ("When the spell ends, you return", "fx", {"op": "trigger", "event": {"event": "effect_ends"},
                                                   "condition": {"pred": "space_occupied"},
                                                   "then": [dmg({"op": "mul", "args": [2, {"var": "feet_moved"}]}, "force", target=SELF,
                                                                note="Shunted to the nearest unoccupied space.")]}),
        ("This spell ends instantly", "rule", {"id": "fails", "on_ethereal_or_non_bordering_plane": True}),
        (HL, "rule", {"id": "targets", "willing_creatures": {"op": "mul", "args": [3, {"op": "sub", "args": [SLOT, 7]}]},
                      "within_feet": 10})]))
    E.append(S("Finger of Death", [
        ("^", "fx", save("con", dmg({"op": "add", "args": ["7d8", 30]}, "necrotic"), half=True, target=creatures(must_see=True))),
        ("A Humanoid killed by this spell", "fx", {"op": "summon", "creature": "dnd5e/creature/zombie", "controller": "summoner",
                                                   "initiative": "own",
                                                   "note": "A Humanoid killed by the spell rises at the start of your next turn and follows your verbal orders."})]))
    E.append(S("Fire Storm", [
        ("^", "fx", save("dex", dmg("7d10", "fire"), half=True,
                         target={"kind": "area", "area": {"shape": "cube", "size_feet": 10, "origin": "point"}, "range": "@range",
                                 "count": 10})),
        ("^", "rule", {"id": "cubes", "max": 10, "contiguous": True}),
        ("Flammable objects in the area", "ref", ["dnd5e/hazard/burning"])]))
    E.append(S("Forcecage", [
        ("^", "rule", {"id": "prison", "immobile": True, "invisible": True, "forms": ["cage", "box"]}),
        ("A prison in the shape of a cage", "rule", {"id": "forms", "cage": {"side_feet": 20, "bar_inches": 0.5, "gap_inches": 0.5},
                                                     "box": {"side_feet": 10, "blocks_matter_and_spells": True}}),
        ("When you cast the spell, any creature", "rule", {"id": "trapping", "inside": "trapped", "partially_inside": "pushed_out"}),
        ("A creature inside the cage can’t leave", "fx", {"op": "trigger", "event": {"event": "tries_teleport_out"},
                                                          "then": [save("cha", ref(SP("forcecage"), note="The magic is wasted."), target=INHERIT,
                                                                        note="On a success it can use that magic to exit.")]}),
        ("A creature inside the cage can’t leave", "rule", {"id": "barrier", "nonmagical_exit": False, "blocks_ethereal": True}),
        ("This spell can’t be dispelled", "rule", {"id": "dispel", "dispel_magic": False})]))
    E.append(S("Magnificent Mansion", [
        ("^", "rule", {"id": "door", "width_feet": 5, "height_feet": 10, "open_close_within_feet": 30, "imperceptible_closed": True}),
        ("Beyond the door", "desc", None),
        ("You can create any floor plan", "rule", {"id": "dwelling", "max_cubes": 50, "cube_feet": 10, "banquet_people": 100,
                                                   "objects_dissipate_if_removed": True}),
        ("A staff of 100", "rule", {"id": "servants", "count": 100, "invulnerable": True, "obey": True, "harm": False,
                                    "leave_dwelling": False}),
        ("When the spell ends, any creatures", "rule", {"id": "end", "occupants_expelled": True})]))
    E.append(S("Mirage Arcane", [
        ("^", "rule", {"id": "illusion", "area_square_miles": 1, "senses": ["sight", "sound", "smell", "touch"]}),
        ("Similarly, you can alter the appearance", "rule", {"id": "structures", "alter_or_add": True, "creatures": False}),
        ("The illusion includes audible", "rule", {"id": "physical", "can_change_difficult_terrain": True,
                                                   "removed_pieces_disappear": True}),
        ("Creatures with Truesight", "rule", {"id": "truesight", "sees_true_form": True, "still_interacts": True})]))
    E.append(S("Plane Shift", [
        ("^", "fx", {"op": "move", "mode": "teleport", "target": creatures(9, willing=True), "note": "You and up to eight willing creatures linking hands."}),
        ("^", "md", md("plane_shift_arrival", "Where exactly in or near the destination do the travelers appear?",
                       "you appear in or near that destination, as determined by the GM.")),
        ("Alternatively, if you know the sigil sequence", "rule", {"id": "circle", "known_teleportation_circle": True,
                                                                   "overflow": "closest_unoccupied_spaces"})]))
    rays = [{"id": c.lower(), "label": c, "roll": str(i + 1), "effects": [
        save("dex", dmg("12d6", t), half=True, target=INHERIT)]} for i, (c, t) in enumerate(
        [("Red", "fire"), ("Orange", "acid"), ("Yellow", "lightning"), ("Green", "poison"), ("Blue", "cold")])]
    rays += [{"id": "indigo", "label": "Indigo", "roll": "6", "effects": [
                save("dex", [cond("restrained", None),
                             {"op": "trigger", "event": {"event": "turn_end", "whose": "target", "which": "each"},
                              "then": [save("con", None, target=INHERIT,
                                            note="Three successes end the condition; three failures: Petrified until freed by an effect like Greater Restoration.")]}],
                     target=INHERIT)]},
             {"id": "violet", "label": "Violet", "roll": "7", "effects": [
                 save("dex", [cond("blinded", None),
                              {"op": "trigger", "event": {"event": "turn_start", "whose": "source"},
                               "then": [save("wis", {"op": "move", "mode": "teleport",
                                                     "note": "To another plane of existence (GM's choice)."}, target=INHERIT,
                                             on_success={"op": "remove_condition", "conditions": [C("blinded")]})]}],
                      target=INHERIT)]},
             {"id": "special", "label": "Special", "roll": "8", "effects": [
                 {"op": "repeat", "times": 2, "then": [ref(SP("prismatic-spray"), note="Roll again, rerolling any 8.")]}]}]
    E.append(S("Prismatic Spray", [
        ("^", "fx", {"op": "choice", "id": "ray", "choose": 1, "chooser": "random", "options": rays,
                     "target": area("cone", 60, "self"), "note": "Roll 1d8 for each creature in the Cone."}),
        ("##### Prismatic Rays", "table", tab("Prismatic Rays", ["1d8", "Ray"])),
        ("##### Prismatic Rays", "md", md("violet_plane", "To which plane is the creature teleported?",
                                          "On a failed save, the condition ends, and the creature teleports to another plane of existence (GM’s choice)."))]))
    E.append(S("Project Image", [
        ("^", "rule", {"id": "copy", "location_seen_before": True, "intangible": True, "ends_on_damage": True}),
        ("You can see through the illusion’s eyes", "fx", {"op": "activation", **MAGIC, "then": [
            {"op": "move", "mode": "move", "distance_feet": 60, "note": "The illusion; it gestures, speaks and behaves as you choose."}]}),
        ("You can see through the illusion’s eyes", "rule", {"id": "senses", "see_and_hear_through": True}),
        ("Physical interaction with the image", "fx", STUDY)]))
    E.append(S("Regenerate", [("^", "fx", [
        heal({"op": "add", "args": ["4d8", 15]}, target=touch()),
        {"op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"}, "duration": "@duration",
         "then": [heal(1, target=INHERIT)]}]),
        ("^", "rule", {"id": "regrow", "severed_parts_regrow_minutes": 2})]))
    E.append(S("Resurrection", [
        ("^", "fx", {"op": "modifier", "stat": "hp", "mode": "set", "value": {"var": "hp_max"}, "target": touch(),
                     "note": "Dead no more than a century, not of old age, and not Undead when it died."}),
        ("The creature returns to life", "rule", {"id": "restoration", "neutralizes_poisons": True, "restores_missing_parts": True}),
        ("Coming back from the dead is an ordeal", "fx", {"op": "modifier", "stat": "d20_test", "mode": "add", "value": -4,
                                                          "note": "Reduced by 1 each time the target finishes a Long Rest."}),
        ("Casting this spell to revive", "fx", {"op": "restrict", "restrictions": ["cast_spells"], "target": SELF,
                                                "duration": {"kind": "until_event", "until": {"event": "long_rest_finished"}},
                                                "when": {"pred": "dead_at_least_days", "args": {"days": 365}},
                                                "note": "You also have Disadvantage on D20 Tests until then."})]))
    E.append(S("Reverse Gravity", [
        ("^", "fx", save("dex", {"op": "move", "mode": "fall", "note": "Falls upward to the top of the Cylinder."},
                         target=area("cylinder", 50),
                         note="On a success the creature grabs a fixed object it can reach.")),
        ("^", "rule", {"id": "cylinder", "radius_feet": 50, "height_feet": 100}),
        ("If a ceiling or an anchored object", "ref", ["dnd5e/hazard/falling"]),
        ("If a ceiling or an anchored object", "rule", {"id": "top", "hover_at_top": True, "fall_when_spell_ends": True})]))
    E.append(S("Sequester", [
        ("^", "fx", [cond("invisible", target=touch(willing=True)),
                     {"op": "restrict", "restrictions": ["targeted_by_divination", "detected_or_viewed_by_magic"], "duration": "@duration"}]),
        ("If the target is a creature", "fx", cond("unconscious", note="Suspended animation: doesn't age or need food, water or air.")),
        ("You can set a condition", "md", md("sequester_end", "Has the end condition occurred?",
                                             "You can set a condition for the spell to end early. The condition can be anything you choose, but it must occur or be visible within 1 mile of the target.")),
        ("You can set a condition", "rule", {"id": "end", "ends_on_damage": True})]))
    E.append(S("Simulacrum", [
        ("^", "rule", {"id": "simulacrum", "original": ["beast", "humanoid"], "within_feet_entire_casting": 10,
                       "statistics_of_original": True, "creature_type": "construct", "hp_max_multiplier": 0.5,
                       "cannot_cast": SP("simulacrum")}),
        ("The simulacrum is Friendly", "rule", {"id": "behavior", "attitude": "dnd5e/attitude/friendly", "acts_on_your_turn": True,
                                                "gains_levels": False, "rests": False}),
        ("If the simulacrum takes damage", "rule", {"id": "repair", "only_during_your_long_rest": True, "gp_per_hp": 100,
                                                    "within_feet": 5}),
        ("The simulacrum lasts until", "rule", {"id": "end", "at_0_hp": "melts", "recast_destroys_previous": True})]))
    symbol = {"op": "choice", "id": "symbol", "choose": 1, "options": [
        {"id": "death", "label": "Death", "effects": [save("con", dmg("10d10", "necrotic"), half=True, target=INHERIT)]},
        {"id": "discord", "label": "Discord", "effects": [save("wis", {"op": "roll_mode", "mode": "disadvantage",
                                                                       "rolls": ["attack_roll", "ability_check"],
                                                                       "duration": {"kind": "minutes", "amount": 1},
                                                                       "note": "It argues and can't communicate meaningfully."}, target=INHERIT)]},
        {"id": "fear", "label": "Fear", "effects": [save("wis", cond("frightened", {"kind": "minutes", "amount": 1},
                                                                     note="Must move at least 30 feet away from the glyph each turn, if able."), target=INHERIT)]},
        {"id": "pain", "label": "Pain", "effects": [save("con", cond("incapacitated", {"kind": "minutes", "amount": 1}), target=INHERIT)]},
        {"id": "sleep", "label": "Sleep", "effects": [save("wis", cond("unconscious", {"kind": "minutes", "amount": 10},
                                                                       note="Wakes if it takes damage or is shaken awake."), target=INHERIT)]},
        {"id": "stunning", "label": "Stunning", "effects": [save("wis", cond("stunned", {"kind": "minutes", "amount": 1}), target=INHERIT)]}]}
    E.append(S("Symbol", [
        ("^", "rule", {"id": "glyph", "max_diameter_feet": 10, "breaks_if_moved_feet": 10}),
        ("The glyph is nearly imperceptible", "rule", {"id": "notice", "check": {"ability": "wis", "skill": "perception", "dc": "spell_save_dc"}}),
        ("When you inscribe the glyph", "rule", {"id": "effect_choice", "options": ["death", "discord", "fear", "pain", "sleep", "stunning"]}),
        ("***Set the Trigger.***", "md", md("symbol_trigger", "Has the glyph's trigger occurred?",
                                           "You decide what triggers the glyph when you cast the spell.")),
        ("You can refine the trigger", "rule", {"id": "refine", "by_creature_type": True, "exemptions": "e.g._password"}),
        ("Once triggered, the glyph glows", "fx", {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"},
                                                   "frequency": {"count": 1, "per": "turn"},
                                                   "duration": {"kind": "minutes", "amount": 10}, "then": [symbol],
                                                   "note": "Also each creature in the Sphere when it activates."}),
        ("Once triggered, the glyph glows", "rule", {"id": "glow", "area": {"shape": "sphere", "radius_feet": 60}, "light": light(dim=60)}),
        ("***Death.***", "sys", ["/effects/0/then/0/options/0"]),
        ("***Discord.***", "sys", ["/effects/0/then/0/options/1"]),
        ("***Fear.***", "sys", ["/effects/0/then/0/options/2"]),
        ("***Pain.***", "sys", ["/effects/0/then/0/options/3"]),
        ("***Sleep.***", "sys", ["/effects/0/then/0/options/4"]),
        ("***Stunning.***", "sys", ["/effects/0/then/0/options/5"])]))
    E.append(S("Teleport", [
        ("^", "fx", {"op": "move", "mode": "teleport", "target": creatures(9, must_see=True, willing=True),
                     "note": "You and up to eight willing creatures, or one Large or smaller object not carried by an unwilling creature."}),
        ("The destination you choose must be known", "fx", {"op": "choice", "id": "outcome", "choose": 1, "chooser": "gm",
                                                            "note": "The GM rolls 1d100 on the Teleportation Outcome table by familiarity.",
                                                            "options": [
            {"id": "mishap", "label": "Mishap", "effects": [dmg("3d10", "force", note="Each teleporting creature or the object; the GM rerolls on the table.")]},
            {"id": "similar_area", "label": "Similar Area", "effects": [ref(SP("teleport"), note="Closest similar place.")]},
            {"id": "off_target", "label": "Off Target", "effects": [{"op": "move", "mode": "teleport", "note": "2d12 miles away; 1d8 for direction."}]},
            {"id": "on_target", "label": "On Target", "effects": [ref(SP("teleport"), note="Where you intended.")]}]}),
        ("##### Teleportation Outcome", "table", tab("Teleportation Outcome", ["Familiarity", "Mishap", "Similar Area", "Off Target", "On Target"])),
        ("***Familiarity.***", "rule", {"id": "familiarity", "levels": ["permanent_circle", "linked_object", "very_familiar", "seen_casually",
                                                                       "viewed_once_or_described", "false_destination"],
                                       "linked_object_months": 6}),
        ("***Mishap.***", "sys", ["/effects/1/options/0"]),
        ("***Similar Area.***", "sys", ["/effects/1/options/1"]),
        ("***Similar Area.***", "md", md("similar_area", "Which similar place do the travelers reach?",
                                         "You appear in the closest similar place.")),
        ("***Off Target.***", "sys", ["/effects/1/options/2"]),
        ("***On Target.***", "sys", ["/effects/1/options/3"])]))
    return E


REGISTRY = {
    "variables": [
        {"id": "rounds_elapsed", "description": "Number of the caster's turns that ended while the spell lasted.", "type": "number", "pages": [122]},
        {"id": "feet_moved", "description": "Distance in feet the creature was moved.", "type": "number", "pages": [129]}],
    "restrictions": [
        {"id": "targeted_by_divination", "description": "The creature can't be targeted by Divination spells.", "pages": [161]},
        {"id": "detected_or_viewed_by_magic", "description": "The creature can't be detected by magic or viewed remotely with magic.", "pages": [161]}],
    "events": [
        {"id": "touches_effect", "description": "A creature touches the spell's effect.", "pages": [122]},
        {"id": "tries_teleport_out", "description": "A creature tries to use teleportation or interplanar travel to leave.", "pages": [133]}],
    "predicates": [
        {"id": "creature_type_in", "description": "The creature's type is one of these (param).", "params": ["types"], "type": "predicate", "pages": [124]},
        {"id": "space_occupied", "description": "The arrival space is occupied.", "type": "predicate", "pages": [129]},
        {"id": "dead_at_least_days", "description": "The creature has been dead at least N days (param).", "params": ["days"], "type": "predicate", "pages": [159]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
