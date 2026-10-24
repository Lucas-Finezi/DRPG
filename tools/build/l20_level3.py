#!/usr/bin/env python3
"""L20 — Level 3 spells (42).

Usage: python3 -I tools/build/l20_level3.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spelllib import (BLOCKED, C, DC, EACH_END, INHERIT, MAGIC, MOD, SELF, SLOT, SP, STUDY, S_for, active,  # noqa: E402
                      all_but, area, attack, cond, creatures, dmg, extra_targets, heal, light, md, ref, save, touch,
                      until_turn, up, updice, write_all)

LOT = "L20"
S = S_for(LOT)
HL = "***Using a Higher-Level Spell Slot.***"
PLANAR5 = ["celestial", "elemental", "fey", "fiend", "undead"]


def entries():
    E = []
    E.append(S("Animate Dead", [
        ("^", "fx", {"op": "choice", "id": "remains", "choose": 1, "options": [
            {"id": "bones", "label": "Pile of bones", "effects": [{"op": "summon", "creature": "dnd5e/creature/skeleton", "controller": "summoner", "initiative": "own"}]},
            {"id": "corpse", "label": "Corpse", "effects": [{"op": "summon", "creature": "dnd5e/creature/zombie", "controller": "summoner", "initiative": "own"}]}],
            "note": "Remains of a Medium or Small Humanoid within range."}),
        ("On each of your turns, you can take a Bonus Action", "fx", {
            "op": "activation", "cost": "bonus_action",
            "then": [ref(SP("animate-dead"), note="Command any or all of your creatures within 60 feet: specific action and movement or a general order.")]}),
        ("On each of your turns, you can take a Bonus Action", "rule", {"id": "no_command", "default": "dodge_and_avoid_harm",
                                                                        "action": "dnd5e/action/dodge", "orders_persist_until_done": True}),
        ("The creature is under your control for 24 hours", "rule", {"id": "control", "hours": 24, "recast_reasserts": 4}),
        (HL, "rule", {"id": "upcast", "additional_creatures": {"op": "mul", "args": [2, {"op": "sub", "args": [SLOT, 3]}]},
                      "each_from_different_remains": True})]))
    E.append(S("Beacon of Hope", [("^", "fx", [
        {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.wis", "death_saving_throw"],
         "target": {"kind": "creature", "range": "@range"},
         "duration": "@duration", "note": "Any number of creatures within range."},
        {"op": "modifier", "stat": "healing_dice", "mode": "set", "value": 0, "duration": "@duration",
         "note": "Regains the maximum number of Hit Points possible from any healing."}])]))
    E.append(S("Bestow Curse", [
        ("^", "fx", save("wis", {"op": "choice", "id": "curse", "choose": 1, "options": [
            {"id": "ability", "label": "Disadvantage with one ability", "effects": [
                {"op": "roll_mode", "mode": "disadvantage", "rolls": ["ability_check", "saving_throw"], "duration": "@duration",
                 "when": {"pred": "roll_uses_ability", "args": {"ability": "chosen.ability"}}}]},
            {"id": "attacks_against_you", "label": "Disadvantage on attacks against you", "effects": [
                {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"], "duration": "@duration",
                 "when": {"pred": "attack_targets_source"}}]},
            {"id": "dodge", "label": "Forced Dodge", "effects": [
                {"op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"}, "duration": "@duration",
                 "condition": {"pred": "in_combat"},
                 "then": [save("wis", ref("dnd5e/action/dodge", note="Forced to take the Dodge action that turn."), target=INHERIT)]}]},
            {"id": "necrotic", "label": "Extra Necrotic damage", "effects": [
                {"op": "trigger", "event": {"event": "damaged_by_source_attack_or_spell"}, "duration": "@duration",
                 "then": [dmg("1d8", "necrotic", target=INHERIT)]}]}]}, target=touch())),
        ("- Choose one ability", "sys", ["/effects/0/on_fail/0/options/0"]),
        ("- The target has Disadvantage on attack rolls", "sys", ["/effects/0/on_fail/0/options/1"]),
        ("- In combat", "sys", ["/effects/0/on_fail/0/options/2"]),
        ("- If you deal damage", "sys", ["/effects/0/on_fail/0/options/3"]),
        (HL, "rule", {"id": "upcast_duration", "by_slot_level": [
            {"slot": 4, "duration": {"kind": "minutes", "amount": 10, "up_to": True, "concentration": True}},
            {"slot": 5, "duration": {"kind": "hours", "amount": 8}}, {"slot": 7, "duration": {"kind": "hours", "amount": 24}},
            {"slot": 9, "duration": {"kind": "until_dispelled"}}]})]))
    E.append(S("Blink", [
        ("^", "fx", {"op": "trigger", "event": {"event": "turn_end", "whose": "self", "which": "each"}, "duration": "@duration",
                     "then": [ref(SP("blink"), note="Roll 1d6: on 4-6, vanish to the Ethereal Plane (the spell ends if already there).")]}),
        ("^", "rule", {"id": "ethereal", "perceive_origin_plane_within_feet": 60, "interacts_only_with_ethereal": True,
                       "imperceptible_without_special_ability": True}),
        ("You return to the other plane", "rule", {"id": "return", "at": ["start_of_next_turn", "spell_ends"],
                                                   "to_unoccupied_space_within_feet": 10, "fallback": "nearest_unoccupied_space"})]))
    E.append(S("Call Lightning", [
        ("^", "rule", {"id": "cloud", "shape": "cylinder", "height_feet": 10, "radius_feet": 60, "must_see_above_you": True}),
        ("When you cast the spell, choose a point", "fx", save("dex", dmg(updice(3, 10, 3), "lightning"), half=True,
                                                               target=area("sphere", 5))),
        ("Until the spell ends, you can take a Magic action", "fx", {"op": "activation", **MAGIC, "then": [
            save("dex", dmg(updice(3, 10, 3), "lightning"), half=True, target=area("sphere", 5))]}),
        ("If you’re outdoors in a storm", "rule", {"id": "storm", "controls_existing_storm": True, "extra_damage": "1d10"}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Clairvoyance", [
        ("^", "rule", {"id": "sensor", "invisible": True, "intangible": True, "invulnerable": True,
                       "location": ["familiar_location", "obvious_unfamiliar_location"]}),
        ("When you cast the spell, choose seeing or hearing", "fx", {"op": "activation", "cost": "bonus_action",
                                                                     "then": [ref(SP("clairvoyance"), note="Switch between seeing and hearing through the sensor.")]}),
        ("A creature that sees the sensor", "rule", {"id": "visible_as", "appearance": "luminous_fist_sized_orb",
                                                     "seen_by": [SP("see-invisibility"), "truesight"]})]))
    E.append(S("Conjure Animals", [
        ("^", "rule", {"id": "pack", "size": "large", "spectral_intangible": True, "form_choice": True}),
        ("You have Advantage on Strength saving throws", "fx", [
            {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.str"], "duration": "@duration",
             "when": {"pred": "within_feet_of_effect", "args": {"feet": 5}}},
            {"op": "trigger", "event": {"event": "moves_on_turn"}, "duration": "@duration",
             "then": [{"op": "move", "mode": "move", "distance_feet": 30, "note": "The pack, to an unoccupied space you can see."}]}]),
        ("Whenever the pack moves within 10 feet", "fx", {
            "op": "trigger", "event": {"event": "creature_within_feet_of_effect"}, "optional": True, "duration": "@duration",
            "frequency": {"count": 1, "per": "turn"},
            "then": [save("dex", dmg(updice(3, 10, 3), "slashing"), target=INHERIT)]}),
        (HL, "sys", ["/effects/2/then/0/on_fail/0/amount"])]))
    E.append(S("Counterspell", [("^", "fx", save("con", ref(SP("counterspell"),
                                                            note="The spell dissipates; the action, Bonus Action or Reaction is wasted; a spell slot isn't expended."),
                                                 target={"kind": "creature"}))]))
    E.append(S("Create Food and Water", [("^", "rule", {
        "id": "create", "food_lb": 45, "water_gallons": 30, "food_spoils_hours": 24,
        "hazards": ["dnd5e/hazard/malnutrition", "dnd5e/hazard/dehydration"]})]))
    E.append(S("Daylight", [
        ("^", "rule", {"id": "sunlight", "area": {"shape": "sphere", "radius_feet": 60}, "light": light(60, 60), "sunlight": True}),
        ("Alternatively, you cast the spell on an object", "rule", {"id": "object", "area": {"shape": "emanation", "size_feet": 60},
                                                                    "opaque_cover_blocks": True}),
        ("If any of this spell’s area overlaps", "rule", {"id": "dispel_darkness", "dispels_darkness_spells_of_level_at_most": 3})]))
    E.append(S("Dispel Magic", [
        ("^", "fx", ref(SP("dispel-magic"), target={"kind": "creature_or_object", "range": "@range"},
                        note="Ends every ongoing spell of level 3 or lower on the target.")),
        ("^", "rule", {"id": "higher_spells", "check": {"ability": "spellcasting", "dc": {"op": "add", "args": [10, {"var": "spell_level"}]}},
                       "for_each_spell_of_level_at_least": 4}),
        (HL, "rule", {"id": "upcast", "auto_end_spell_level_at_most": SLOT})]))
    E.append(S("Fear", [
        ("^", "fx", save("wis", [{"op": "restrict", "restrictions": ["hold_items"], "note": "Drops whatever it is holding."},
                                 cond("frightened")], target=area("cone", 30, "self"))),
        ("A Frightened creature takes the Dash action", "fx", [
            {"op": "trigger", "event": {"event": "turn_start", "whose": "target", "which": "each"}, "duration": "@duration",
             "then": [ref("dnd5e/action/dash", note="Moves away from you by the safest route unless there is nowhere to move.")]},
            {"op": "trigger", "event": {"event": "turn_end", "whose": "target", "which": "each"}, "duration": "@duration",
             "condition": {"not": {"pred": "has_line_of_sight_to_source"}},
             "then": [save("wis", None, target=INHERIT, on_success={"op": "end_effect", "scope": "this_entry_on_target"})]}])]))
    E.append(S("Fireball", [
        ("^", "fx", save("dex", dmg(updice(8, 6, 3), "fire"), half=True, target=area("sphere", 20))),
        ("Flammable objects in the area", "ref", ["dnd5e/hazard/burning"]),
        ("Flammable objects in the area", "rule", {"id": "ignite", "objects_in_area": True, "not_worn_or_carried": True}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Fly", [
        ("^", "fx", {"op": "speed", "movement": "fly", "mode": "max", "value": 60, "hover": True, "target": touch(willing=True),
                     "duration": "@duration"}),
        ("^", "rule", {"id": "end", "falls_if_aloft": True, "rule": "dnd5e/hazard/falling"}),
        (HL, "rule", {"id": "targets", "count": extra_targets(3)})]))
    E.append(S("Gaseous Form", [
        ("^", "rule", {"id": "form", "misty_cloud": True, "includes_gear": True, "ends_on": ["0_hp", "magic_action_to_end"]}),
        ("While in this form", "fx", [
            {"op": "speed", "movement": "fly", "mode": "set", "value": 10, "hover": True, "duration": "@duration",
             "note": "Its only method of movement."},
            {"op": "defense", "kind": "resistance", "damage_types": ["bludgeoning", "piercing", "slashing"], "duration": "@duration"},
            {"op": "defense", "kind": "immunity", "conditions": [C("prone")], "duration": "@duration"},
            {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.str", "saving_throw.dex", "saving_throw.con"],
             "duration": "@duration"}]),
        ("While in this form", "rule", {"id": "movement", "enter_other_creature_space": True, "narrow_openings": True,
                                        "liquids_as_solid": True}),
        ("The target can’t talk", "fx", {"op": "restrict", "restrictions": ["speak", "hold_items", "attack", "cast_spells"],
                                         "duration": "@duration", "note": "Carried objects can't be dropped or used."}),
        (HL, "rule", {"id": "targets", "count": extra_targets(3)})]))
    E.append(S("Glyph of Warding", [
        ("^", "rule", {"id": "glyph", "max_diameter_feet": 10, "surface_or_closable_object": True,
                       "breaks_if_moved_feet": 10}),
        ("The glyph is nearly imperceptible", "rule", {"id": "notice", "check": {"ability": "wis", "skill": "perception", "dc": "spell_save_dc"}}),
        ("When you inscribe the glyph", "rule", {"id": "type", "choose": ["explosive_rune", "spell_glyph"]}),
        ("***Set the Trigger.***", "md", md("glyph_trigger", "Has the glyph's trigger occurred?",
                                           "You decide what triggers the glyph when you cast the spell.")),
        ("You can refine the trigger", "rule", {"id": "refine", "by_creature_type": True, "exemptions": "e.g._password"}),
        ("***Explosive Rune.***", "fx", save("dex", dmg(updice(5, 8, 3), ["acid", "cold", "fire", "lightning", "thunder"]),
                                            half=True, target={"kind": "area", "area": {"shape": "sphere", "size_feet": 20, "origin": "point"}},
                                            note="Damage type chosen when creating the glyph.")),
        ("***Spell Glyph.***", "rule", {"id": "spell_glyph", "stored_spell_max_level": {"op": "max", "args": [3, SLOT]},
                                       "stored_spell_targets": "single_creature_or_area", "no_immediate_effect": True}),
        ("When the glyph is triggered, the stored spell", "rule", {"id": "release", "targets_triggering_creature": True,
                                                                    "area_centered_on_it": True, "concentration_full_duration": True}),
        (HL, "sys", ["/effects/0/on_fail/0/amount", "rule:spell_glyph"])]))
    E.append(S("Haste", [
        ("^", "fx", [
            {"op": "speed", "movement": "walk", "mode": "multiply", "value": 2, "target": creatures(must_see=True, willing=True),
             "duration": "@duration"},
            {"op": "modifier", "stat": "ac", "mode": "add", "value": 2, "duration": "@duration"},
            {"op": "roll_mode", "mode": "advantage", "rolls": ["saving_throw.dex"], "duration": "@duration"},
            {"op": "modifier", "stat": "actions_this_turn", "mode": "add", "value": 1, "duration": "@duration",
             "note": "Only Attack (one attack), Dash, Disengage, Hide or Utilize."}]),
        ("When the spell ends", "fx", {"op": "trigger", "event": {"event": "effect_ends"}, "then": [
            cond("incapacitated", until_turn("turn_end", "target")),
            {"op": "speed", "movement": "walk", "mode": "set", "value": 0, "duration": until_turn("turn_end", "target")}]})]))
    E.append(S("Hypnotic Pattern", [
        ("^", "fx", save("wis", [cond("charmed"), cond("incapacitated"),
                                 {"op": "speed", "movement": "walk", "mode": "set", "value": 0, "duration": "@duration"}],
                         target=area("cube", 30),
                         note="Only creatures that can see the pattern.")),
        ("The spell ends for an affected creature", "rule", {"id": "ends", "ends_on": ["takes_damage", "shaken_by_action"]})]))
    E.append(S("Lightning Bolt", [
        ("^", "fx", save("dex", dmg(updice(8, 6, 3), "lightning"), half=True, target=area("line", 100, "self"))),
        ("^", "rule", {"id": "line", "length_feet": 100, "width_feet": 5}),
        (HL, "sys", ["/effects/0/on_fail/0/amount"])]))
    E.append(S("Magic Circle", [
        ("^", "rule", {"id": "circle", "shape": "cylinder", "radius_feet": 10, "height_feet": 20}),
        ("Choose one or more of the following types", "rule", {"id": "types", "choose_from": PLANAR5}),
        ("- The creature can’t willingly enter", "fx", {"op": "restrict", "restrictions": ["enter_area_nonmagically"],
                                                        "duration": "@duration", "note": "Teleportation or interplanar travel into it requires a successful Charisma save."}),
        ("- The creature has Disadvantage", "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["attack_roll"],
                                                   "duration": "@duration", "when": {"pred": "target_in_area"}}),
        ("- Targets within the Cylinder", "fx", {"op": "defense", "kind": "immunity", "conditions": [C("charmed"), C("frightened")],
                                                 "duration": "@duration", "note": "Also can't be possessed by the creature."}),
        ("Each time you cast this spell", "rule", {"id": "reverse", "optional": True, "keeps_creature_inside": True}),
        (HL, "rule", {"id": "duration", "hours": up(1, 3)})]))
    E.append(S("Major Image", [
        ("^", "rule", {"id": "image", "max_cube_feet": 20, "senses": ["sight", "sound", "smell", "temperature"],
                       "damage_or_conditions": False}),
        ("If you are within range of the illusion", "fx", {"op": "activation", **MAGIC, "then": [
            {"op": "move", "mode": "move", "note": "The image, to any spot within range; appearance and sounds can change."}]}),
        ("Physical interaction with the image", "rule", {"id": "physical_interaction", "reveals_illusion": True}),
        ("Physical interaction with the image", "fx", STUDY),
        (HL, "rule", {"id": "permanent", "slot_at_least": 4, "duration": {"kind": "until_dispelled"}, "concentration": False})]))
    E.append(S("Mass Healing Word", [
        ("^", "fx", heal({"op": "add", "args": [updice(2, 4, 3), MOD]}, target=creatures(6, must_see=True))),
        (HL, "sys", ["/effects/0/amount"])]))
    E.append(S("Meld into Stone", [
        ("^", "rule", {"id": "meld", "must_touch_stone": True, "includes_equipment": True, "undetectable_nonmagically": True}),
        ("While merged with the stone", "fx", {"op": "roll_mode", "mode": "disadvantage", "rolls": ["ability_check.wis"],
                                               "duration": "@duration", "note": "Wisdom (Perception) checks to hear outside sounds; can't see outside."}),
        ("While merged with the stone", "rule", {"id": "merged", "can_cast_on_self": True, "exit_movement_feet": 5,
                                                 "otherwise_cannot_move": True}),
        ("Minor physical damage to the stone", "fx", [
            {"op": "trigger", "event": {"event": "stone_partially_destroyed"},
             "then": [dmg("6d6", "force", target=SELF), cond("prone", None, target=SELF)]},
            {"op": "trigger", "event": {"event": "stone_destroyed"},
             "then": [dmg(50, "force", target=SELF), cond("prone", None, target=SELF)]}])]))
    E.append(S("Nondetection", [("^", "rule", {
        "id": "hide", "targets": ["willing_creature", "place_or_object_up_to_10_feet"],
        "immune_to": ["divination_targeting", "magical_scrying_sensors"]})]))
    E.append(S("Phantom Steed", [
        ("^", "rule", {"id": "steed", "size": "large", "equipment": ["saddle", "bit", "bridle"], "equipment_vanishes_beyond_feet": 10}),
        ("For the duration, you or a creature you choose", "fx", {"op": "summon", "creature": "dnd5e/creature/riding-horse",
                                                                  "controller": "summoner", "initiative": "shared",
                                                                  "note": "Speed 100 feet; 13 miles per hour; ends early if it takes any damage; 1 minute to dismount at the end."})]))
    E.append(S("Plant Growth", [
        ("^", "rule", {"id": "mode_by_casting_time", "action": "overgrowth", "8_hours": "enrichment"}),
        ("***Overgrowth.***", "rule", {"id": "overgrowth", "area": {"shape": "sphere", "radius_feet": 100},
                                      "movement_cost_multiplier": 4, "exclusions": "any_areas"}),
        ("***Enrichment.***", "rule", {"id": "enrichment", "radius_miles": 0.5, "days": 365, "harvest_multiplier": 2,
                                      "once_per_year": True})]))
    E.append(S("Protection from Energy", [("^", "fx", {"op": "defense", "kind": "resistance",
                                                       "damage_types": [{"choose_from": ["acid", "cold", "fire", "lightning", "thunder"]}],
                                                       "target": touch(willing=True), "duration": "@duration"})]))
    E.append(S("Remove Curse", [("^", "rule", {"id": "remove", "ends_all_curses": True,
                                               "cursed_magic_item": "curse_remains_attunement_broken",
                                               "rule": "dnd5e/curse/cursed-magic-items"})]))
    E.append(S("Revivify", [("^", "fx", {"op": "modifier", "stat": "hp", "mode": "set", "value": 1, "target": touch(),
                                         "note": "A creature dead for less than a minute revives; not death from old age; missing parts aren't restored."})]))
    E.append(S("Sending", [
        ("^", "rule", {"id": "message", "max_words": 25, "recipient": "met_or_described", "reply": "immediate",
                       "understood": True}),
        ("You can send the message across any distance", "rule", {"id": "range", "any_distance": True,
                                                                  "other_plane_failure_percent": 5, "know_if_failed": True}),
        ("Upon receiving your message", "rule", {"id": "block", "hours": 8, "learn_blocked": True})]))
    E.append(S("Sleet Storm", [
        ("^", "rule", {"id": "storm", "area": {"shape": "cylinder", "radius_feet": 20, "height_feet": 40}, "heavily_obscured": True,
                       "douses_exposed_flames": True}),
        ("Ground in the Cylinder is Difficult Terrain", "fx", {
            "op": "trigger", "event": {"event": "enters_or_starts_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
            "duration": "@duration",
            "then": [save("dex", [cond("prone", None), {"op": "end_effect", "scope": "concentration"}], target=INHERIT)]})]))
    E.append(S("Slow", [
        ("^", "fx", save("wis", [
            {"op": "speed", "movement": "walk", "mode": "multiply", "value": 0.5, "duration": "@duration"},
            {"op": "modifier", "stat": "ac", "mode": "add", "value": -2, "duration": "@duration"},
            {"op": "modifier", "stat": "saving_throw.dex", "mode": "add", "value": -2, "duration": "@duration"},
            {"op": "restrict", "restrictions": ["take_reactions", "action_and_bonus_action_same_turn"], "duration": "@duration",
             "note": "Only one attack with the Attack action."}],
            target=area("cube", 40), repeat=EACH_END, note="Up to six creatures of your choice in the Cube.")),
        ("An affected target’s Speed is halved", "rule", {"id": "somatic_failure", "spell_failure_percent": 25,
                                                          "applies_to": "spells_with_somatic_component"}),
        ("An affected target repeats the save", "sys", ["/effects/0/repeat"])]))
    E.append(S("Speak with Dead", [
        ("^", "rule", {"id": "corpse", "requires_mouth": True, "fails_if_undead_at_death": True, "cooldown_days": 10}),
        ("Until the spell ends, you can ask", "md", md("answers", "What does the corpse answer?",
                                                       "The corpse knows only what it knew in life, including the languages it knew. Answers are usually brief, cryptic, or repetitive, and the corpse is under no compulsion to offer a truthful answer if you are antagonistic toward it or it recognizes you as an enemy.",
                                                       reason="narrative")),
        ("Until the spell ends, you can ask", "rule", {"id": "questions", "max": 5, "no_new_information": True})]))
    E.append(S("Speak with Plants", [
        ("^", "rule", {"id": "plants", "area": {"shape": "emanation", "size_feet": 30, "immobile": True}}),
        ("^", "md", md("plant_answers", "What do the plants know about the past day?",
                       "You can question plants about events in the spell’s area within the past day, gaining information about creatures that have passed, weather, and other circumstances.",
                       reason="narrative")),
        ("You can also turn Difficult Terrain", "rule", {"id": "terrain", "plant_difficult_terrain": "ordinary_or_reverse"}),
        ("The spell doesn’t enable plants", "rule", {"id": "movement", "uproot": False, "move_branches": True}),
        ("If a Plant creature is in the area", "rule", {"id": "plant_creatures", "communicate": True})]))
    E.append(S("Spirit Guardians", [
        ("^", "rule", {"id": "appearance", "good_or_neutral": ["angelic", "fey"], "evil": "fiendish"}),
        ("When you cast this spell, you can designate", "fx", [
            {"op": "speed", "movement": "walk", "mode": "multiply", "value": 0.5, "target": area("emanation", 15, "self"),
             "duration": "@duration", "note": "Creatures not designated as unaffected."},
            {"op": "trigger", "event": {"event": "enters_or_ends_turn_in_area"}, "frequency": {"count": 1, "per": "turn"},
             "duration": "@duration", "note": "Also when the Emanation enters its space.",
             "then": [save("wis", dmg(updice(3, 8, 3), ["radiant", "necrotic"],
                                      note="Radiant if you are good or neutral, Necrotic if evil."), half=True, target=INHERIT)]}]),
        (HL, "sys", ["/effects/1/then/0/on_fail/0/amount"])]))
    E.append(S("Stinking Cloud", [
        ("^", "rule", {"id": "cloud", "area": {"shape": "sphere", "radius_feet": 20}, "heavily_obscured": True,
                       "dispersed_by": "strong_wind", "example": SP("gust-of-wind")}),
        ("Each creature that starts its turn", "fx", {"op": "trigger", "event": {"event": "turn_start", "whose": "any"},
                                                      "condition": {"pred": "in_spell_area"}, "duration": "@duration",
                                                      "then": [save("con", [cond("poisoned", until_turn("turn_end", "target")),
                                                                            {"op": "restrict", "restrictions": ["take_actions", "take_bonus_actions"],
                                                                             "duration": until_turn("turn_end", "target")}], target=INHERIT)]})]))
    E.append(S("Tiny Hut", [
        ("^", "rule", {"id": "hut", "area": {"shape": "emanation", "size_feet": 10}, "stationary": True,
                       "fails_if_cant_contain_all": True}),
        ("Creatures and objects within the Emanation", "rule", {"id": "barrier", "occupants_pass": True, "others_barred": True,
                                                                "blocks_spells_of_level_at_most": 3}),
        ("The atmosphere inside", "rule", {"id": "interior", "comfortable_dry": True, "light_choice": ["dim", "darkness"],
                                           "opaque_outside": True, "transparent_inside": True}),
        ("The spell ends early", "rule", {"id": "ends", "ends_on": ["you_leave", "cast_again"]})]))
    E.append(S("Tongues", [("^", "rule", {"id": "tongues", "understand_any_spoken_or_signed": True,
                                          "understood_by_any_creature_with_a_language": True})]))
    E.append(S("Vampiric Touch", [
        ("^", "fx", attack("melee_spell", [dmg(updice(3, 6, 3), "necrotic"),
                                           heal({"op": "div", "args": [{"var": "damage_amount"}, 2]}, target=SELF)],
                           target={"kind": "creature", "range": {"kind": "touch"}})),
        ("Until the spell ends, you can make the attack again", "fx", {"op": "activation", **MAGIC, "frequency": {"count": 1, "per": "turn"},
                                                                       "then": [ref(SP("vampiric-touch"), note="Repeat the attack.")]}),
        (HL, "sys", ["/effects/0/on_hit/0/amount"])]))
    E.append(S("Water Breathing", [("^", "fx", {"op": "modifier", "stat": "breathe_underwater", "mode": "set", "value": 1,
                                                "target": creatures(10, willing=True), "duration": "@duration"})]))
    E.append(S("Water Walk", [
        ("^", "fx", {"op": "modifier", "stat": "water_walk", "mode": "set", "value": 1, "target": creatures(10, willing=True),
                     "duration": "@duration", "note": "Liquid surfaces as solid ground; molten lava can still deal heat damage."}),
        ("An affected target must take a Bonus Action", "rule", {"id": "enter_liquid", "cost": "bonus_action",
                                                                 "falling_passes_through": True})]))
    E.append(S("Wind Wall", [
        ("^", "rule", {"id": "wall", "length_feet": 50, "height_feet": 15, "thickness_feet": 1, "continuous_path": True}),
        ("When the wall appears", "fx", save("str", dmg("4d8", "bludgeoning"), half=True,
                                             target={"kind": "area", "area": {"shape": "line", "size_feet": 50, "origin": "point"},
                                                     "range": "@range"})),
        ("The strong wind keeps fog", "rule", {"id": "effects", "keeps_away_gases": True, "blocks_small_flyers": True,
                                               "ordinary_projectiles_miss": True, "boulders_and_siege_unaffected": True,
                                               "gaseous_form_blocked": True})]))
    return E


REGISTRY = {
    "stats": [
        {"id": "healing_dice", "description": "How healing dice are resolved for the creature (0 = maximum possible).", "pages": [113]},
        {"id": "water_walk", "description": "The creature can move across liquid surfaces as solid ground.", "pages": [172]}],
    "restrictions": [
        {"id": "attack", "description": "The creature can't attack.", "pages": [134]},
        {"id": "enter_area_nonmagically", "description": "The creature can't willingly enter the area by nonmagical means.", "pages": [146]},
        {"id": "action_and_bonus_action_same_turn", "description": "The creature can take either an action or a Bonus Action on its turn, not both.", "pages": [163]}],
    "events": [
        {"id": "damaged_by_source_attack_or_spell", "description": "The source deals damage to the target with an attack roll or a spell.", "pages": [113]},
        {"id": "moves_on_turn", "description": "The creature moves on its turn.", "pages": [118]},
        {"id": "creature_within_feet_of_effect", "description": "The effect moves within range of a creature, or a creature enters or ends its turn within range of it.", "pages": [118]},
        {"id": "effect_ends", "description": "The effect ends.", "pages": [138]},
        {"id": "stone_partially_destroyed", "description": "The stone is partially destroyed or changes shape so the creature no longer fits.", "pages": [148]},
        {"id": "stone_destroyed", "description": "The stone is destroyed or transmuted into a different substance.", "pages": [148]}],
    "predicates": [
        {"id": "attack_targets_source", "description": "The attack targets the source.", "type": "predicate", "pages": [113]},
        {"id": "within_feet_of_effect", "description": "The creature is within N feet (param) of the effect.", "params": ["feet"], "type": "predicate", "pages": [118]},
        {"id": "has_line_of_sight_to_source", "description": "The creature has line of sight to the source.", "type": "predicate", "pages": [130]},
        {"id": "target_in_area", "description": "The attack's target is within the spell's area.", "type": "predicate", "pages": [146]}],
}

if __name__ == "__main__":
    write_all(entries(), REGISTRY, LOT)
